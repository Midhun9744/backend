from app import db

class Device(db.Model):
    __tablename__ = "devices"

    id = db.Column(db.Integer, primary_key=True)
    household_id = db.Column(
        db.Integer,
        db.ForeignKey("households.id"),
        nullable=False
    )

    device_name = db.Column(db.String(100))
    device_type = db.Column(db.String(20))  # esp32 / raspberry_pi
    mac_address = db.Column(db.String(50), unique=True)

    status = db.Column(db.String(20), default="offline")
    last_seen = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
