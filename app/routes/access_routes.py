from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from app import db
from app.models.access_permission import AccessPermission
from app.models.household import Household
from app.models.user import User


access_bp = Blueprint(
    "access",
    __name__,
    url_prefix="/api/access"
)

# =================================================
# 1) CAREGIVER REQUEST ACCESS USING INVITE CODE
# =================================================
@access_bp.route("/request", methods=["POST"])
@jwt_required()
def request_access():

    try:
        print("\n===== ACCESS REQUEST DEBUG =====")

        # ⭐ GET USER ID FROM JWT
        user_id = int(get_jwt_identity())
        print("User ID:", user_id)

        data = request.get_json()
        print("JSON:", data)

        if not data:
            return {"error": "Invalid JSON"}, 400

        code = data.get("invite_code")

        if not code:
            return {"error": "Invite code required"}, 400
        
        code = code.strip()

        # Find household
        house = Household.query.filter_by(
            invite_code=code
        ).first()

        if not house:
            return {"error": "Invalid invite code"}, 404

        # Prevent duplicate request
        existing = AccessPermission.query.filter_by(
            household_id=house.id,
            user_id=user_id
        ).first()

        if existing:
            return {"message": "Request already exists"}, 200

        # Create request
        req = AccessPermission(
            household_id=house.id,
            user_id=user_id,
            role="caregiver",
            status="pending"
        )

        db.session.add(req)
        db.session.commit()

        print("Request saved successfully")

        return {"message": "Request sent"}, 200

    except Exception as e:
        print("🔥 ERROR:", str(e))
        return {"error": str(e)}, 500


# =================================================
# 2) SENIOR — VIEW PENDING REQUESTS
# =================================================
@access_bp.route("/pending", methods=["GET"])
@jwt_required()
def pending_requests():

    senior_id = get_jwt_identity()

    house = Household.query.filter_by(
        senior_user_id=senior_id
    ).first()

    if not house:
        return {"error": "No household found"}, 404

    requests = AccessPermission.query.filter_by(
        household_id=house.id,
        status="pending"
    ).all()

    result = []

    for r in requests:
        user = User.query.get(r.user_id)

        result.append({
            "request_id": r.id,
            "user_id": r.user_id,
            "name": user.full_name,
            "role": r.role,
            "requested_at": r.requested_at
        })

    return result, 200


# =================================================
# 3) SENIOR — VIEW APPROVED USERS
# =================================================
@access_bp.route("/approved", methods=["GET"])
@jwt_required()
def approved_users():

    senior_id = get_jwt_identity()

    house = Household.query.filter_by(
        senior_user_id=senior_id
    ).first()

    if not house:
        return {"error": "No household found"}, 404

    users = AccessPermission.query.filter_by(
        household_id=house.id,
        status="approved"
    ).all()

    result = []

    for u in users:
        user = User.query.get(u.user_id)

        result.append({
            "id": u.id,
            "user_id": u.user_id,
            "name": user.full_name,
            "role": u.role,
            "enabled": u.enabled
        })

    return result, 200


# =================================================
# 4) SENIOR — APPROVE REQUEST
# =================================================
@access_bp.route("/approve/<int:req_id>", methods=["POST"])
@jwt_required()
def approve_request(req_id):

    senior_id = int(get_jwt_identity())

    req = AccessPermission.query.get(req_id)

    if not req:
        return {"error": "Request not found"}, 404

    house = Household.query.get(req.household_id)

    if house.senior_user_id != senior_id:
        return {"error": "Unauthorized"}, 403

    req.status = "approved"
    req.approved_by = senior_id
    req.approved_at = datetime.now()
    req.enabled = True

    db.session.commit()

    return {"message": "Access approved"}, 200


# =================================================
# 5) SENIOR — REJECT REQUEST
# =================================================
@access_bp.route("/reject/<int:req_id>", methods=["POST"])
@jwt_required()
def reject_request(req_id):

    senior_id = get_jwt_identity()

    req = AccessPermission.query.get(req_id)

    if not req:
        return {"error": "Request not found"}, 404

    house = Household.query.get(req.household_id)

    if house.senior_user_id != senior_id:
        return {"error": "Unauthorized"}, 403

    req.status = "rejected"
    req.approved_by = senior_id
    req.approved_at = datetime.now()

    db.session.commit()

    return {"message": "Request rejected"}, 200


# =================================================
# 6) TOGGLE MONITORING ACCESS (Switch ON/OFF)
# =================================================
@access_bp.route("/toggle/<int:perm_id>", methods=["POST"])
@jwt_required()
def toggle_access(perm_id):

    senior_id = get_jwt_identity()

    perm = AccessPermission.query.get(perm_id)

    if not perm:
        return {"error": "Permission not found"}, 404

    house = Household.query.get(perm.household_id)

    if house.senior_user_id != senior_id:
        return {"error": "Unauthorized"}, 403

    data = request.get_json()
    enabled = data.get("enabled", True)

    perm.enabled = enabled

    db.session.commit()

    return {"message": "Access updated"}, 200


# =================================================
# 7) CAREGIVER — CHECK MY REQUEST STATUS
# =================================================
@access_bp.route("/my-status", methods=["GET"])
@jwt_required()
def my_status():

    user_id = get_jwt_identity()

    req = AccessPermission.query.filter_by(
        user_id=user_id
    ).first()

    if not req:
        return {"status": "none"}, 200

    return {
        "status": req.status,
        "enabled": req.enabled
    }, 200
