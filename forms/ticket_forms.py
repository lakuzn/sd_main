from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    TextAreaField,
    DateField,
    SubmitField,
    SelectField,
    SelectMultipleField,
)
from wtforms.validators import DataRequired, Length, Optional


class TicketForm(FlaskForm):
    description = TextAreaField(
        "Описание проблемы",
        validators=[
            DataRequired(message="Поле обязательно"),
            Length(
                min=1,
                max=2000,
                message="Описание должно быть от 1 до 2000 символов.",
            ),
        ],
    )

    desired_deadline = DateField(
        "Желаемый срок выполнения",
        validators=[Optional()],
        format="%Y-%m-%d",
    )

    submit = SubmitField("Отправить заявку")


class RouteTicketForm(FlaskForm):
    document_number = StringField(
        "Официальный документ (СЗ, Приказ)",
    )

    priority = SelectField(
        "Приоритет",
        choices=[
            ("Низкий", "Низкий"),
            ("Средний", "Средний"),
            ("Высокий", "Высокий"),
        ],
        validators=[DataRequired()],
    )

    category_ids = SelectMultipleField(
        "Категории",
        coerce=int,
        validators=[DataRequired()],
    )

    executor_ids = SelectMultipleField(
        "Исполнители",
        coerce=int,
    )

    department_id = SelectField(
        "Отдел",
        coerce=int,
        validators=[Optional()],
    )

    submit = SubmitField("Сохранить параметры")


class ReassignTicketForm(FlaskForm):
    executor_ids = SelectMultipleField(
        "Новые исполнители",
        coerce=int,
        validators=[DataRequired()],
    )

    submit = SubmitField("Переназначить")
