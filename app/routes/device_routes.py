from flask import Blueprint, request
from app import db
from app.models.device import Device

device_bp = Blueprint("device", __name__)

# Register Device
@device_bp.route("/register", methods=["POST"])
def register_device():

    data = request.json

    device = Device(
        household_id=data["household_id"],
        device_name=data["name"],
        device_type=data["type"],
        mac_address=data["mac"]
    )

    db.session.add(device)
    db.session.commit()

    return {"message": "Device registered"}
