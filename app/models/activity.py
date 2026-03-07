from app import db

class Activity(db.Model):
    __tablename__ = "activities"

    id = db.Column(db.Integer, primary_key=True)

    person_id = db.Column(
        db.Integer,
        db.ForeignKey("monitored_persons.id"),
        nullable=False
    )

    activity_type = db.Column(db.String(50), nullable=False)
    confidence = db.Column(db.Float)

    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)

    recorded_at = db.Column(db.DateTime, server_default=db.func.now())
