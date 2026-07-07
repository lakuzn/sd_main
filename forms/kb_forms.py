from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired


class ArticleForm(FlaskForm):
    title = StringField("Заголовок статьи", validators=[DataRequired()])
    category_id = SelectField("Категория", coerce=int, validators=[DataRequired()])

    content = TextAreaField("Текст статьи", validators=[DataRequired()])

    is_staff_only = BooleanField("Только для сотрудников (скрыть от пользователей)")
    submit = SubmitField("Опубликовать статью")
