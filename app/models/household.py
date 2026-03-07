from app import db

class Household(db.Model):
    __tablename__ = "households"

    id = db.Column(db.Integer, primary_key=True)

    house_name = db.Column(
        db.String(100),
        nullable=False
    )

    address = db.Column(db.Text)

    senior_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        unique=True,
        nullable=False
    )

    invite_code = db.Column(
        db.String(20),
        unique=True,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    # -----------------------------
    # Relationships (recommended)
    # -----------------------------
    senior = db.relationship(
        "User",
        backref="household",
        lazy=True
    )

    monitored_persons = db.relationship(
        "MonitoredPerson",
        backref="household",
        cascade="all, delete-orphan"
    )
