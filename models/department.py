from app.extensions import db


head_managed_departments = db.Table(
    "head_managed_departments",
    db.Column(
        "user_id",
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "department_id",
        db.Integer,
        db.ForeignKey("departments.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Department(db.Model):
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

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

    @staticmethod
    def resolve_subtree(all_departments, base_ids):
        base_ids = {int(i) for i in base_ids if i is not None}
        if not base_ids:
            return set()

        base_names = [
            d.name for d in all_departments if d.id in base_ids and d.name
        ]

        result = set(base_ids)
        for dept in all_departments:
            if not dept.name:
                continue
            for base_name in base_names:
                if dept.name == base_name or dept.name.startswith(base_name + "."):
                    result.add(dept.id)
                    break
        return result
