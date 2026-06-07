# Файл с настройками (который будет читать для нас .env)

import os
from dotenv import load_dotenv

# Загрузка переменных из .env
load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SERCET_KEY")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")

    # Отключение лишней функции слежения за изменениями
    SQLALCHEMY_TRACK_MODIFICATIONS = False
