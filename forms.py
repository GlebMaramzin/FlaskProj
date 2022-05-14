from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DateField, BooleanField
from wtforms.validators import DataRequired, Length


class LoginForm(FlaskForm):
    login = StringField("Логин: ", validators=[Length(min=1, max=12)])
    password = PasswordField("Пароль: ", validators=[DataRequired(), Length(min=1, max=50)])
    submit = SubmitField("Войти")


class CreateProjectForm(FlaskForm):
    title = StringField("Название проекта: ", validators=[Length(min=1, max=100)])
    desc = StringField("Описание проекта: ")
    deadline = DateField("Дата окончания проекта: ")
    submit = SubmitField("Создать проект")


class CreateTaskForm(FlaskForm):
    title = StringField("Название задачи: ")
    desc = StringField("Описание задачи: ")
    deadline = DateField("Дата окончания задачи: ")
    isPriority = BooleanField("Приоритетная задача: ")
    submit = SubmitField("Создать задачу")

