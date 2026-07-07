from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    email = StringField(
        "Почта",
        validators=[
            DataRequired(message="Введите адрес почты"),
        ],
    )

    password = PasswordField(
        "Пароль",
        validators=[
            DataRequired(message="Введите пароль"),
        ],
    )

    submit = SubmitField("Войти")
