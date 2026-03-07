from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from app.models.activity import Activity
from app.models.access_permission import AccessPermission
from app.models.monitored_person import MonitoredPerson
from app.models.household import Household
from app.models.user import User

# -------------------------------------------------
# Blueprint
# -------------------------------------------------
activity_bp = Blueprint(
    "activity",
    __name__,
    url_prefix="/api/activity"
)

# -------------------------------------------------
# TEMP STORAGE FOR LATEST ACTIVITY (LIVE STATE)
# Updated by Raspberry Pi / IoT device
# -------------------------------------------------
latest_activity = {
    "activity": None,
    "confidence": 0,
    "timestamp": None,
    "is_fall": False
}


# =================================================
# 1️⃣ UPDATE ACTIVITY (IoT → Backend)
# =================================================
@activity_bp.route("/update", methods=["POST"])
def update_activity():

    from app import db

    data = request.get_json()

    if not data or "activity" not in data:
        return {"error": "Invalid data"}, 400

    activity_name = data["activity"]
    confidence = data.get("confidence", 0)
    person_id = data.get("person_id")

    is_fall = activity_name.lower() == "fall"

    # -------------------------------------------------
    # UPDATE LIVE STATE
    # -------------------------------------------------
    latest_activity["activity"] = activity_name
    latest_activity["confidence"] = confidence
    latest_activity["timestamp"] = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    latest_activity["is_fall"] = is_fall

    # -------------------------------------------------
    # STORE ONLY FALL EVENTS
    # -------------------------------------------------
    if is_fall and person_id:

        fall_record = Activity(
            person_id=person_id,
            activity_type="Fall",
            confidence=confidence,
            start_time=datetime.now()
        )

        db.session.add(fall_record)
        db.session.commit()

    return {"message": "Activity updated"}, 200


# =================================================
# 2️⃣ GET LATEST ACTIVITY (Mobile App)
# =================================================
@activity_bp.route("/latest", methods=["GET"])
@jwt_required()
def get_latest_activity():

    user_id = int(get_jwt_identity())

    from app.models.user import User
    from app.models.household import Household
    from app.models.access_permission import AccessPermission

    user = User.query.get(user_id)

    # ----------------------------
    # SENIOR → Always allowed
    # ----------------------------
    if user.role == "senior":
        pass

    # ----------------------------
    # CAREGIVER / MEMBER
    # ----------------------------
    else:
        permission = AccessPermission.query.filter_by(
            user_id=user_id,
            status="approved"
        ).first()

        if not permission:
            return {"error": "Access denied"}, 403

        if permission.enabled is False:
            return {"error": "Access disabled by senior"}, 403

    # ----------------------------
    # RETURN LIVE DATA
    # ----------------------------
    if latest_activity["activity"] is None:
        return {
            "activity": None,
            "message": "No activity data yet"
        }, 200

    return latest_activity, 200

# =================================================
# 3️⃣ GET ACTIVITY HISTORY (FROM DATABASE)
# Senior + Caregiver + Member
# =================================================
@activity_bp.route("/history", methods=["GET"])
@jwt_required()
def get_activity_history():

    user_id = int(get_jwt_identity())

    user = User.query.get(user_id)

    if not user:
        return {"error": "User not found"}, 404

    # -------------------------------------------------
    # CASE 1 — SENIOR USER
    # -------------------------------------------------
    if user.role == "senior":

        house = Household.query.filter_by(
            senior_user_id=user_id
        ).first()

        if not house:
            return [], 200

        household_id = house.id

    # -------------------------------------------------
    # CASE 2 — CAREGIVER / MEMBER
    # -------------------------------------------------
    else:

        permission = AccessPermission.query.filter_by(
            user_id=user_id,
            status="approved"
        ).first()

        if not permission:
            return {"error": "No household access"}, 403
        
        if permission.enabled is False:
            return {"error": "Access disabled"}, 403

        household_id = permission.household_id

    # -------------------------------------------------
    # FIND MONITORED PERSON
    # -------------------------------------------------
    person = MonitoredPerson.query.filter_by(
        household_id=household_id
    ).first()

    if not person:
        return [], 200

    # -------------------------------------------------
    # FETCH FALL HISTORY
    # -------------------------------------------------
    activities = Activity.query.filter_by(
        person_id=person.id
    ).order_by(Activity.start_time.desc()).limit(50).all()

    result = []

    for act in activities:
        result.append({
            "activity": act.activity_type,
            "confidence": act.confidence,
            "time": act.start_time.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        })

    return result, 200