"""
ЗАПУСК (сервер):
source .venv/bin/activate
python3 update_user_roles.py --dry-run
python3 update_user_roles.py --apply

deactivate - выход из venv

Скрипт для массового обновления ролей пользователей по ФИО.
Запускать в контексте приложения Flask.

Пример использования:
    python update_user_roles.py

Или с аргументами командной строки:
    python update_user_roles.py --dry-run  # только показать, что изменится
    python update_user_roles.py --apply    # применить изменения
"""

import os
import sys
import argparse
from pathlib import Path

# Добавляем путь к проекту в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

from app import create_app
from app.extensions import db
from app.models.user import User


# Список пользователей для обновления
# Формат: {"ФИО": "новая_роль"}
USER_ROLE_MAP = {
    "Маринин Евгений Иванович": "admin",
    "Кузнецов Леонид Алексеевич": "admin",
    "Поздеев Алексей Васильевич": "head",
    # 9400
    "Богатов Вадим Александрович": "head",
    "Карташова Ольга Александровна": "executor",
    # 9401
    "Мухина Марина Николаевна": "classifier",
    "Красильников Александр Александрович": "executor",
    "Терентьев Никита Сергеевич": "executor",
    # 9410
    "Терентьев Александр Сергеевич": "head",
    "Курочкин Сергей Николаевич": "executor",
    "Таршин Эдуард Аркадьевич": "executor",
    "Кузнецов Антон Алексеевич": "executor",
    "Хоршев Владимир Авенирович": "executor",
    "Сафронов Денис Андреевич": "executor",
    "Ананченко Алексей Львович": "executor",
    "Щеглов Максим Михайлович": "executor",
    "Юрьев Иван Викторович": "executor",
    "Карташов Николай Андреевич": "executor",
    "Лобанова Елена Владимировна": "executor",
    "Евдокимова Марина Алибековна": "executor",
    "Кулясова Диана Андреевна": "executor",
    # 9420
    "Соловьёв Владислав Юрьевич": "head",
    "Кудряшов Александр Сергеевич": "executor",
    "Носова Юлия Николаевна": "executor",
    "Пылина Татьяна Геннадьевна": "executor",
    "Симаков Виктор Андреевич": "executor",
    "Михайлина Анна Валентиновна": "executor",
    "Молькова Юлия Олеговна": "executor",
    "Плеханов Алексей Николаевич": "executor",
    "Шведов Андрей Иванович": "executor",
    "Ловков Артемий Сергеевич": "executor",
    "Самарина Анна Михайловна": "executor",
    "Кокоткина Надежда Юрьевна": "executor",
    "Назарова Ирина Константиновна": "executor",
    "Терехина Ирина Александровна": "executor",
    "Перепелова Светлана Александровна": "executor",
    "Степанова Лидия Анатольевна": "executor",
    # 9430
    "Цветкова Ксения Евгеньевна": "executor",
    "Степанова Лидия Анатольевна": "executor",
    "Сальникова Кристина Станиславовна": "executor",
    "Шевнин Георгий Игоревич": "executor",
    "Бухонова Елена Николаевна": "executor",
    # 9440
    "Николаев Алексей Игоревич": "head",
    # 9441
    # 9442
    "Зуевский Иван Максимович": "executor",
    "Питерцев Иван Александрович": "executor",
    # 9443
    "Лежнина Екатерина Александровна": "executor",
    "Панфилов Вадим Алексеевич": "executor",
}

# Доступные роли
VALID_ROLES = {"admin", "classifier", "executor", "head", "user"}


def update_user_roles(dry_run=True):
    """
    Обновляет роли пользователей по списку ФИО.

    Args:
        dry_run (bool): если True, только показывает что изменится, не сохраняет в БД
    """
    app = create_app()

    with app.app_context():
        print("=" * 80)
        print("ОБНОВЛЕНИЕ РОЛЕЙ ПОЛЬЗОВАТЕЛЕЙ")
        print("=" * 80)

        if dry_run:
            print("🏁 РЕЖИМ: ТОЛЬКО ПРОСМОТР (изменения НЕ будут сохранены)")
        else:
            print("⚠️  РЕЖИМ: ПРИМЕНЕНИЕ ИЗМЕНЕНИЙ")
        print()

        updated_count = 0
        not_found = []
        invalid_roles = []
        already_have_role = []

        for full_name, new_role in USER_ROLE_MAP.items():
            print(f"Обработка: {full_name}")

            # Проверка валидности роли
            if new_role not in VALID_ROLES:
                print(
                    f"  ❌ НЕВАЛИДНАЯ РОЛЬ: '{new_role}' (доступны: {', '.join(VALID_ROLES)})"
                )
                invalid_roles.append((full_name, new_role))
                continue

            # Поиск пользователя
            user = User.query.filter_by(full_name=full_name).first()

            if not user:
                print(f"  ❌ ПОЛЬЗОВАТЕЛЬ НЕ НАЙДЕН")
                not_found.append(full_name)
                continue

            old_role = user.role

            if old_role == new_role:
                print(f"  ⏭️  Роль уже '{new_role}', изменений не требуется")
                already_have_role.append((full_name, new_role))
                continue

            print(
                f"  📝 {old_role} -> {new_role} (ID: {user.id}, username: {user.username})"
            )

            if not dry_run:
                user.role = new_role
                db.session.add(user)

            updated_count += 1

        # Применяем изменения, если не dry_run
        if not dry_run and updated_count > 0:
            try:
                db.session.commit()
                print(
                    f"\n✅ Изменения успешно сохранены в БД ({updated_count} пользователей)"
                )
            except Exception as e:
                db.session.rollback()
                print(f"\n❌ Ошибка при сохранении изменений: {e}")
                return False
        elif dry_run and updated_count > 0:
            print(
                f"\n🔍 Изменения НЕ сохранены (dry-run режим). Будет обновлено {updated_count} пользователей."
            )

        # Итоговый отчёт
        print("\n" + "=" * 80)
        print("ИТОГОВЫЙ ОТЧЁТ")
        print("=" * 80)
        print(f"✅ Обновлено: {updated_count}")
        print(f"⏭️  Уже имеют роль: {len(already_have_role)}")
        print(f"❌ Не найдено: {len(not_found)}")
        print(f"❌ Невалидные роли: {len(invalid_roles)}")

        if not_found:
            print("\nНе найдены:")
            for name in not_found:
                print(f"  - {name}")

        if invalid_roles:
            print("\nНевалидные роли:")
            for name, role in invalid_roles:
                print(f"  - {name}: {role}")

        if already_have_role:
            print("\nУже имеют нужную роль:")
            for name, role in already_have_role:
                print(f"  - {name}: {role}")

        return True


def interactive_mode():
    """Интерактивный режим для ввода списка пользователей"""
    print("Интерактивный режим обновления ролей")
    print("Вводите пользователей в формате: ФИО, роль")
    print("Для завершения введите пустую строку")
    print("Доступные роли:", ", ".join(VALID_ROLES))
    print()

    user_roles = {}
    while True:
        line = input("> ").strip()
        if not line:
            break

        parts = line.split(",", 1)
        if len(parts) != 2:
            print("  ❌ Неверный формат. Используйте: ФИО, роль")
            continue

        full_name = parts[0].strip()
        role = parts[1].strip()

        if role not in VALID_ROLES:
            print(f"  ❌ Невалидная роль: {role}. Доступны: {', '.join(VALID_ROLES)}")
            continue

        user_roles[full_name] = role
        print(f"  ✅ Добавлен: {full_name} -> {role}")

    if not user_roles:
        print("Список пуст, завершаем")
        return

    print("\nСписок пользователей для обновления:")
    for name, role in user_roles.items():
        print(f"  {name} -> {role}")

    confirm = input("\nПрименить изменения? (y/n): ").strip().lower()
    if confirm == "y":
        # Временно заменяем USER_ROLE_MAP
        global USER_ROLE_MAP
        USER_ROLE_MAP = user_roles
        update_user_roles(dry_run=False)
    else:
        print("Отменено")


def main():
    parser = argparse.ArgumentParser(description="Обновление ролей пользователей")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Только показать что изменится, не сохранять в БД",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Применить изменения (по умолчанию dry-run)",
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Интерактивный режим ввода списка пользователей",
    )

    args = parser.parse_args()

    if args.interactive:
        interactive_mode()
    else:
        dry_run = not args.apply  # по умолчанию dry-run, если не указан --apply
        update_user_roles(dry_run=dry_run)


if __name__ == "__main__":
    main()
