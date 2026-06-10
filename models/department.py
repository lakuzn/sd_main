from app.extensions import db


class Department(db.Model):
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

    # Кто начальник этого отдела?
    head_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", use_alter=True, name="fk_dept_head"),
        nullable=True,
    )

    # Связи
    head = db.relationship("User", foreign_keys=[head_id])
    employees = db.relationship(
        "User", foreign_keys="User.department_id", back_populates="department"
    )
