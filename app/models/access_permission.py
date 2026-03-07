from app import db

class AccessPermission(db.Model):
    __tablename__ = "access_permissions"

    id = db.Column(db.Integer, primary_key=True)

    household_id = db.Column(
        db.Integer,
        db.ForeignKey("households.id"),
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    role = db.Column(db.String(20))

    status = db.Column(
        db.String(20),
        default="pending"
    )

    enabled = db.Column(
        db.Boolean,
        default=False
    )

    approved_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id")
    )

    requested_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    approved_at = db.Column(db.DateTime)
