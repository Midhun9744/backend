from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db

from app.models.household import Household
from app.models.monitored_person import MonitoredPerson
from app.models.user import User

import random
import string


# =================================================
# CREATE BLUEPRINT
# =================================================
household_bp = Blueprint(
    "household",
    __name__,
    url_prefix="/api/household"
)


# =================================================
# HELPER — GENERATE INVITE CODE
# =================================================
def generate_code(length=6):
    chars = string.ascii_uppercase + string.digits

    while True:
        code = "HME-" + "".join(
            random.choice(chars) for _ in range(length)
        )

        # ensure invite code is unique
        exists = Household.query.filter_by(
            invite_code=code
        ).first()

        if not exists:
            return code


# =================================================
# CREATE HOUSEHOLD + MONITORED PERSON
# =================================================
@household_bp.route("/create", methods=["POST"])
@jwt_required()
def create_household():

    # ----------------------------------
    # GET CURRENT USER FROM JWT
    # ----------------------------------
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if not user:
        return {"error": "User not found"}, 404

    print("\n===== USER DEBUG =====")
    print("JWT USER ID:", user_id)
    print("USER ROLE:", user.role)
    print("======================\n")


    # ----------------------------------
    # ALLOW ONLY SENIOR USERS
    # ----------------------------------
    if user.role != "senior":
        return {"error": "Only senior can create household"}, 403


    # ----------------------------------
    # PREVENT MULTIPLE HOUSEHOLDS
    # ----------------------------------
    existing = Household.query.filter_by(
        senior_user_id=user_id
    ).first()

    if existing:
        return {
            "error": "Household already exists",
            "invite_code": existing.invite_code
        }, 400


    # ----------------------------------
    # DEBUG REQUEST
    # ----------------------------------
    print("\n===== DEBUG REQUEST START =====")

    print("Headers:", dict(request.headers))
    print("Raw Data:", request.data)
    print("Content-Type:", request.content_type)

    data = request.get_json(force=True, silent=True)

    print("Parsed JSON:", data)

    print("===== DEBUG REQUEST END =====\n")


    # ----------------------------------
    # VALIDATE JSON
    # ----------------------------------
    if not data:
        return {"error": "Invalid or missing JSON"}, 400

    house_name = data.get("house_name")
    person_name = data.get("person_name")

    if not house_name or not person_name:
        return {
            "error": "house_name and person_name are required"
        }, 400


    invite_code = generate_code()


    try:

        # ----------------------------------
        # CREATE HOUSEHOLD
        # ----------------------------------
        household = Household(
            house_name=house_name,
            address=data.get("address"),
            senior_user_id=user_id,
            invite_code=invite_code
        )

        db.session.add(household)
        db.session.commit()


        # ----------------------------------
        # CREATE MONITORED PERSON
        # ----------------------------------
        person = MonitoredPerson(
            household_id=household.id,
            full_name=person_name,
            age=data.get("age"),
            gender=data.get("gender"),
            medical_notes=data.get("medical_notes")
        )

        db.session.add(person)
        db.session.commit()


        return {
            "message": "Household created successfully",
            "household_id": household.id,
            "invite_code": invite_code
        }, 200


    except Exception as e:

        db.session.rollback()

        print("DB ERROR:", str(e))

        return {"error": str(e)}, 500