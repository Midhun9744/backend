from app import db

class MonitoredPerson(db.Model):
    __tablename__ = "monitored_persons"

    id = db.Column(db.Integer, primary_key=True)
    household_id = db.Column(
        db.Integer,
        db.ForeignKey("households.id"),
        nullable=False
    )

    full_name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    medical_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
