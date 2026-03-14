from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from app import db
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
# LIVE ACTIVITY STATE
# -------------------------------------------------
latest_activity = {
    "activity": None,
    "confidence": 0,
    "timestamp": None,
    "is_fall": False,
    "static_alert": False
}

last_activity = None
last_change_time = None

STATIC_ACTIVITIES = ["standing", "sitting", "lying"]


# =================================================
# UPDATE ACTIVITY (IoT → Backend)
# =================================================
@activity_bp.route("/update", methods=["POST"])
def update_activity():

    global last_activity, last_change_time

    data = request.get_json()

    print("Received activity:", data)

    if not data or "activity" not in data:
        return {"error": "Invalid data"}, 400

    activity_name = data["activity"].lower()
    confidence = data.get("confidence", 0)
    person_id = data.get("person_id")

    now = datetime.now()

    is_fall = activity_name == "fall"
    static_alert = False


    # -------------------------------------------------
    # STATIC ACTIVITY ALERT (120 seconds)
    # -------------------------------------------------
    if activity_name in STATIC_ACTIVITIES:

        if last_activity != activity_name:
            last_activity = activity_name
            last_change_time = now

        else:
            duration = (now - last_change_time).total_seconds()

            if duration >= 120:
                static_alert = True

    else:
        last_activity = activity_name
        last_change_time = now


    # -------------------------------------------------
    # UPDATE LIVE STATE
    # -------------------------------------------------
    latest_activity["activity"] = activity_name
    latest_activity["confidence"] = confidence
    latest_activity["timestamp"] = now.strftime("%Y-%m-%d %H:%M:%S")
    latest_activity["is_fall"] = is_fall
    latest_activity["static_alert"] = static_alert


    # -------------------------------------------------
    # STORE EVERY ACTIVITY IN DATABASE
    # -------------------------------------------------
    if person_id:

        activity_record = Activity(
            person_id=person_id,
            activity_type=activity_name,
            confidence=confidence,
            start_time=now
        )

        db.session.add(activity_record)
        db.session.commit()

        print("Stored activity:", activity_name)


    return {"message": "Activity stored"}, 200


# =================================================
# GET LATEST ACTIVITY (Mobile App)
# =================================================
@activity_bp.route("/latest", methods=["GET"])
@jwt_required()
def get_latest_activity():

    user_id = int(get_jwt_identity())

    user = User.query.get(user_id)

    if not user:
        return {"error": "User not found"}, 404


    # -------------------------------------------------
    # CAREGIVER / MEMBER ACCESS CHECK
    # -------------------------------------------------
    if user.role != "senior":

        permission = AccessPermission.query.filter_by(
            user_id=user_id,
            status="approved"
        ).first()

        if not permission:
            return {"error": "Access denied"}, 403

        if permission.enabled is False:
            return {"error": "Access disabled by senior"}, 403


    if latest_activity["activity"] is None:

        return {
            "activity": None,
            "message": "No activity data yet"
        }, 200


    return latest_activity, 200


# =================================================
# GET ACTIVITY HISTORY
# =================================================
@activity_bp.route("/history", methods=["GET"])
@jwt_required()
def get_activity_history():

    user_id = int(get_jwt_identity())

    user = User.query.get(user_id)

    if not user:
        return {"error": "User not found"}, 404


    # -------------------------------------------------
    # SENIOR
    # -------------------------------------------------
    if user.role == "senior":

        house = Household.query.filter_by(
            senior_user_id=user_id
        ).first()

        if not house:
            return [], 200

        household_id = house.id


    # -------------------------------------------------
    # CAREGIVER / MEMBER
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
    # FETCH ACTIVITY HISTORY
    # -------------------------------------------------
    activities = Activity.query.filter_by(
        person_id=person.id
    ).order_by(Activity.start_time.desc()).limit(200).all()


    result = []

    for act in activities:

        result.append({
            "activity": act.activity_type,
            "confidence": act.confidence,
            "time": act.start_time.strftime("%Y-%m-%d %H:%M:%S")
        })

    return result, 200