from flask import Blueprint, request
from app import db
from app.models.alert import Alert

alert_bp = Blueprint("alert", __name__)

# Create Alert (e.g., Fall detected)
@alert_bp.route("/create", methods=["POST"])
def create_alert():

    data = request.json

    alert = Alert(
        person_id=data["person_id"],
        alert_type=data["type"],
        message=data["message"]
    )

    db.session.add(alert)
    db.session.commit()

    return {"message": "Alert created"}
