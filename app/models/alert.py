from app import db

class Alert(db.Model):
    __tablename__ = "alerts"

    id = db.Column(db.Integer, primary_key=True)

    person_id = db.Column(
        db.Integer,
        db.ForeignKey("monitored_persons.id"),
        nullable=False
    )

    activity_id = db.Column(
        db.Integer,
        db.ForeignKey("activities.id")
    )

    alert_type = db.Column(db.String(30))
    message = db.Column(db.Text)

    created_at = db.Column(db.DateTime, server_default=db.func.now())
