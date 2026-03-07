from app import db

class AlertRecipient(db.Model):
    __tablename__ = "alert_recipients"

    id = db.Column(db.Integer, primary_key=True)

    alert_id = db.Column(
        db.Integer,
        db.ForeignKey("alerts.id"),
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    is_read = db.Column(db.Boolean, default=False)
    delivered_at = db.Column(db.DateTime)
