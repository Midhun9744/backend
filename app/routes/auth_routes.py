from flask import Blueprint, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import db

from app.models.user import User
from app.models.household import Household
from app.models.access_permission import AccessPermission


auth_bp = Blueprint("auth", __name__)


# =================================================
# REGISTER USER
# =================================================
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.json

    if User.query.filter_by(email=data["email"]).first():
        return {"error": "Email already exists"}, 400

    user = User(
        full_name=data["name"],
        email=data["email"],
        phone=data.get("phone"),
        password_hash=generate_password_hash(data["password"]),
        role=data["role"]  # senior / caregiver / member
    )

    db.session.add(user)
    db.session.commit()

    return {"message": "Registration successful"}, 200


# =================================================
# LOGIN USER
# =================================================
# =================================================
# LOGIN USER
# =================================================
@auth_bp.route("/login", methods=["POST"])
def login():

    data = request.json

    user = User.query.filter_by(email=data["email"]).first()

    if not user or not check_password_hash(
        user.password_hash, data["password"]
    ):
        return {"error": "Invalid credentials"}, 401

    # 🔐 Create JWT token
    token = create_access_token(
        identity=str(user.id)  # must be string
    )

    response = {
        "token": token,
        "role": user.role,
        "user_id": user.id
    }

    # =================================================
    # 👴 SENIOR FLOW
    # =================================================
    if user.role == "senior":

        household = Household.query.filter_by(
            senior_user_id=user.id
        ).first()

        response["setup_complete"] = (
            household is not None
        )

    # =================================================
    # 👩‍⚕️ CAREGIVER / MEMBER FLOW
    # =================================================
    else:

        permission = AccessPermission.query.filter_by(
            user_id=user.id
        ).first()

        if permission:

            response["approved"] = (
                permission.status == "approved"
            )

            response["request_pending"] = (
                permission.status == "pending"
            )

        else:
            response["approved"] = False
            response["request_pending"] = False

    return response, 200

# =================================================
# GET CURRENT USER PROFILE
# =================================================
@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user = User.query.get(get_jwt_identity())

    return {
        "id": user.id,
        "name": user.full_name,
        "email": user.email,
        "role": user.role
    }, 200
