from app import create_app
from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash


def seed():

    app = create_app()
    with app.app_context():

        from app.models import User, Category, KnowledgeArticle, Department

        db.drop_all()
        db.create_all()
        print("Пересоздаем базы.")
        print("Загружаем тестовые данные.")

        # 0. Отделы
        dep_941 = Department(
            name="Отдел 941",
        )
        dep_942 = Department(
            name="Отдел 942",
        )
        dep_943 = Department(
            name="Отдел 943",
        )
        dep_944 = Department(
            name="Отдел 944",
        )
        db.session.add_all([dep_941, dep_942, dep_943, dep_944])
        db.session.flush()
        print("Отделы добавлены.")

        # 1. Пользователи

        user1 = User(
            full_name="Иван Петров",
            email="user1@example.com",
            phone="17-90",
            role="user",
            position="Инженер-программист",
            department_id=dep_944.id,
        )
        user1.set_password("111")

        user2 = User(
            full_name="Марина Смирнова",
            email="executor2@example.com",
            phone="19-84",
            role="executor",
            position="Ведущий специалист",
            department_id=dep_942.id,
        )
        user2.set_password("222")

        user3 = User(
            full_name="Дмитрий Цыганов",
            email="admin3@example.com",
            position="Ведущий аналитик",
            role="admin",
            department_id=dep_942.id,
        )
        user3.set_password("333")

        user4 = User(
            full_name="Корсаков Петр Александрович",
            email="head4@example.com",
            position="Начальник отдела 942",
            role="head",
            department_id=dep_942.id,
        )
        user4.set_password("444")

        user5 = User(
            full_name="Бурденко Даниил Петрович",
            email="user5@example.com",
            phone="30-33",
            position="Ведущий системный администратор",
            role="user",
            department_id=dep_941.id,
        )
        user5.set_password("555")

        user6 = User(
            full_name="Анна Гурьянова",
            email="class6@example.com",
            phone="25-17-3",
            position="Старший аналитик",
            role="classifier",
            department_id=dep_941.id,
        )
        user6.set_password("666")

        user7 = User(
            full_name="Федор Кузьмин",
            email="executor7@example.com",
            phone="45-49",
            position="Старший специалист",
            role="executor",
            department_id=dep_943.id,
        )
        user7.set_password("777")

        db.session.add_all([user1, user2, user3, user4, user5, user6, user7])
        db.session.flush()
        print("Пользователи добавлены.")

        # 2. Категории

        category1 = Category(name="ПО и Доступы")

        category2 = Category(name="Документооборот")

        category3 = Category(name="Почта")

        category4 = Category(name="Оборудование (ПК, Принтеры)")

        category5 = Category(name="Сеть")

        db.session.add_all([category1, category2, category3, category4, category5])
        db.session.flush()
        print("Категории добавлены.")

        # 4. База знаний
        if KnowledgeArticle.query.count() == 0:

            article1 = KnowledgeArticle(
                title="Как изменить пароль в Windows",
                content="1. Нажмите Ctrl+Alt+Del"
                "2. Выберите Изменить пароль."
                "3.Введите старый и новый пароль.",
                category_id=1,
                author_id=user3.id,
            )

            article2 = KnowledgeArticle(
                title="Как изменить пароль в Outlook",
                content="Измените пароль в Windows.",
                category_id=3,
                author_id=user3.id,
            )

            db.session.add_all([article1, article2])
            db.session.flush()
            print("Инструкции добавлены.")
        else:
            print("Инструкции уже есть в БД. Пропускаем.")

        db.session.commit()
        print("База данных заполнена.")


if __name__ == "__main__":
    seed()
