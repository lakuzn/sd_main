"""Инициализация базы данных для боевого сервера.

В отличие от seed_data.py (который ЗАПОЛНЯЕТ базу тестовыми данными и
предварительно всё удаляет), этот скрипт только СОЗДАЁТ таблицы в пустой базе.

Дополнительно можно создать один локальный аккаунт администратора —
«запасной вход» на случай, если вход через Kerberos ещё не настроен.
Логин/пароль берутся из переменных окружения:
    BOOTSTRAP_ADMIN_EMAIL, BOOTSTRAP_ADMIN_PASSWORD
Если они не заданы — админ не создаётся.

Запуск:
    python init_db.py
"""

import os

from app import create_app
from app.extensions import db


def main():
    app = create_app()
    with app.app_context():
        from app.models import User

        db.create_all()
        print("Таблицы созданы (или уже существовали).")

        # Необязательный запасной локальный администратор
        admin_email = os.environ.get("BOOTSTRAP_ADMIN_EMAIL")
        admin_password = os.environ.get("BOOTSTRAP_ADMIN_PASSWORD")

        if admin_email and admin_password:
            existing = User.query.filter_by(email=admin_email).first()
            if existing:
                print(f"Администратор {admin_email} уже существует — пропускаем.")
            else:
                admin = User(
                    full_name="Локальный администратор",
                    email=admin_email,
                    role="admin",
                    is_active=True,
                )
                admin.set_password(admin_password)
                db.session.add(admin)
                db.session.commit()
                print(f"Создан запасной локальный администратор: {admin_email}")
        else:
            print(
                "Запасной администратор не создан "
                "(не заданы BOOTSTRAP_ADMIN_EMAIL / BOOTSTRAP_ADMIN_PASSWORD)."
            )


if __name__ == "__main__":
    main()
