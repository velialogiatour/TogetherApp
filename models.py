from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import ARRAY
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    last_seen = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


    def set_password(self, password):
        """Хэширование пароля перед сохранением"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Проверка пароля"""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User{self.name}, Email{self.email}>'

class Questionnaire(db.Model):
    __tablename__ = 'questionnaires'

    questionnaire_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    profile_photo = db.Column(db.String(255))  # один путь к главному фото
    additional_photos = db.Column(ARRAY(db.String))  # массив путей к дополнительным фото
    description = db.Column(db.Text)
    interests = db.Column(db.Text)
    zodiac_sign = db.Column(db.String(20))
    height = db.Column(db.Integer)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    user = db.relationship('User', backref=db.backref('questionnaire', uselist=False))

class PasswordResetToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)

class Like(db.Model):
    __tablename__ = 'likes'

    like_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    liked_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_blocked = db.Column(db.Boolean, default=False)
    is_new = db.Column(db.Boolean, default=True)

    # Ограничение уникальности: один лайк от user_id к liked_user_id
    __table_args__ = (
        db.UniqueConstraint('user_id', 'liked_user_id', name='unique_like'),
    )

    user = db.relationship('User', foreign_keys=[user_id], backref='likes_given')
    liked_user = db.relationship('User', foreign_keys=[liked_user_id], backref='likes_received')


class Messages(db.Model):
    __tablename__ = 'messages'

    message_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    message = db.Column(db.Text, nullable=False)

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')


class Settings(db.Model):
    __tablename__ = 'settings'

    setting_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)

    is_deactivated = db.Column(db.Boolean, default=False)  # деактивация аккаунта
    notifications_enabled = db.Column(db.Boolean, default=True)  # включены ли уведомления

    user = db.relationship('User', backref=db.backref('settings', uselist=False))


class Matches(db.Model):
    __tablename__ = 'matches'

    match_id = db.Column(db.Integer, primary_key=True)
    user_one_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user_two_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    matched_ad = db.Column(db.String)
