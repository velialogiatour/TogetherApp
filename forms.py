from flask_wtf import FlaskForm
from wtforms import PasswordField, BooleanField, StringField, IntegerField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Email, ValidationError, EqualTo, NumberRange
from flask_wtf.file import FileField, FileAllowed, MultipleFileField
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

class QuestionnaireForm(FlaskForm):
    age = IntegerField('Возраст', validators=[DataRequired(), NumberRange(min=18, max=99)])
    gender = SelectField('Пол', choices=[('Мужчина', 'Мужчина'), ('Женщина', 'Женщина')], validators=[DataRequired()])
    country = StringField('Страна', validators=[DataRequired()])
    city = StringField('Город', validators=[DataRequired()])
    height = IntegerField('Рост (см)', validators=[NumberRange(min=100, max=250)])
    zodiac_sign = StringField('Знак зодиака')
    interests = TextAreaField('Интересы')
    description = TextAreaField('О себе')

    profile_photo = FileField('Фото профиля', validators=[FileAllowed(['jpg', 'jpeg', 'png'], 'Только изображения')])
    additional_photos = MultipleFileField('Дополнительные фото', validators=[FileAllowed(['jpg', 'jpeg', 'png'], 'Только изображения')])

    submit = SubmitField('Создать анкету')
