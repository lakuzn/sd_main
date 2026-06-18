# На случай, если нам понадобится локально добавить пользователей.

from app import create_app
from app.extensions import db
from app.models import User


# === ОТРЕДАКТИРУЙТЕ ЭТОТ СПИСОК ===
# (ФИО, email, пароль, роль, должность, телефон)
USERS = [
    (
        "Тестов Тест Тестович",
        "test.user@example.com",
        "test12345",
        "user",
        "Инженер",
        "10-01",
    ),
    (
        "Класс Ификатор",
        "test.class@example.com",
        "class12345",
        "classifier",
        "Старший аналитик",
        "10-02",
    ),
    (
        "Испол Нитель",
        "test.exec@example.com",
        "exec12345",
        "executor",
        "Специалист",
        "10-03",
    ),
    (
        "Началь Ник",
        "test.head@example.com",
        "head12345",
        "head",
        "Начальник отдела",
        "10-04",
    ),
    (
        "Админ Истратор",
        "test.admin@example.com",
        "admin12345",
        "admin",
        "Администратор",
        "10-05",
    ),
]

VALID_ROLES = {"user", "classifier", "executor", "head", "admin"}


def main():
    app = create_app()
    with app.app_context():
        added = 0
        for full_name, email, password, role, position, phone in USERS:
            if role not in VALID_ROLES:
                print(f"ПРОПУСК: у {email} недопустимая роль '{role}'.")
                continue

            if User.query.filter_by(email=email).first():
                print(f"ПРОПУСК: {email} уже есть в базе.")
                continue

            user = User(
                full_name=full_name,
                email=email,
                role=role,
                position=position,
                phone=phone,
                is_active=True,
            )
            user.set_password(password)  # пароль хранится в виде безопасного хэша
            db.session.add(user)
            added += 1
            print(f"ДОБАВЛЕН: {email}  (роль: {role})")

        db.session.commit()
        print(f"Готово. Добавлено новых пользователей: {added}.")


if __name__ == "__main__":
    main()
