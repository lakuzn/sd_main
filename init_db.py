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

        # 2 локальных администратора
        admin1_email = os.environ.get("BOOTSTRAP_ADMIN1_EMAIL")
        admin1_password = os.environ.get("BOOTSTRAP_ADMIN1_PASSWORD")

        admin2_email = os.environ.get("BOOTSTRAP_ADMIN2_EMAIL")
        admin2_password = os.environ.get("BOOTSTRAP_ADMIN2_PASSWORD")

        if admin1_email and admin1_password:
            existing = User.query.filter_by(email=admin1_email).first()
            if existing:
                print(f"Администратор {admin1_email} уже существует — пропускаем.")
            else:
                admin1 = User(
                    full_name="Локальный администратор",
                    email=admin1_email,
                    role="admin",
                    is_active=True,
                )
                admin1.set_password(admin1_password)
                db.session.add(admin1)
                db.session.commit()
                print(f"Создан запасной локальный администратор: {admin1_email}")
        else:
            print(
                "Запасной администратор 1 не создан "
                "(не заданы BOOTSTRAP_ADMIN_EMAIL / BOOTSTRAP_ADMIN_PASSWORD)."
            )

        if admin2_email and admin2_password:
            existing = User.query.filter_by(email=admin2_email).first()
            if existing:
                print(f"Администратор {admin2_email} уже существует — пропускаем.")
            else:
                admin2 = User(
                    full_name="Локальный администратор",
                    email=admin2_email,
                    role="admin",
                    is_active=True,
                )
                admin2.set_password(admin2_password)
                db.session.add(admin2)
                db.session.commit()
                print(f"Создан запасной локальный администратор: {admin2_email}")
        else:
            print(
                "Запасной администратор 2 не создан "
                "(не заданы BOOTSTRAP_ADMIN_EMAIL / BOOTSTRAP_ADMIN_PASSWORD)."
            )


if __name__ == "__main__":
    main()
