from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, ValidationError, EqualTo
from models import User


class RegisterForm(FlaskForm):
    name = StringField('Имя', validators=[DataRequired(), Length(max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6, max=12)])
    submit = SubmitField('Зарегистрироваться')

    def validate_email(self, field):
        user = User.query.filter_by(email=field.data).first()
        if user:
            raise ValidationError('Этот email уже зарегистрирован.')

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Пароль", validators=[DataRequired()])
    remember = BooleanField("Запомнить меня")
    submit = SubmitField("Войти")

    def validate_email(self, field):
        user = User.query.filter_by(email=field.data).first()
        if not user:
            raise ValidationError("Этот email не зарегистрирован.")


class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Отправить ссылку для восстановления')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Новый пароль', validators=[
        DataRequired(message="Введите новый пароль"),
        Length(min=8, message="Пароль должен содержать минимум 8 символов")
    ])

    confirm_password = PasswordField('Подтвердите пароль', validators=[
        DataRequired(message="Повторите пароль"),
        EqualTo('password', message="Пароли не совпадают")
    ])

    submit = SubmitField('Изменить пароль')

class QuestionForm(FlaskForm):
    pass