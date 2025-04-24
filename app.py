from datetime import datetime, timedelta, timezone

from flask import Flask, render_template, redirect, url_for, flash, session, request
from flask_wtf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegisterForm, LoginForm, ForgotPasswordForm, ResetPasswordForm
from models import db, User, PasswordResetToken, Like
from config import Connect
from flask_mail import Message, Mail
import secrets

app = Flask(__name__)
app.config.from_object(Connect)
db.init_app(app)
csrf = CSRFProtect(app)
app.config['MAIL_SERVER'] = 'smtp.yourmailserver.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@example.com'
app.config['MAIL_PASSWORD'] = 'your-email-password'
mail = Mail(app)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            session["user_id"] = user.id
            flash("Вход выполнен успешно!", "success")
            return redirect(url_for("basepage"))
        else:
            flash("Неверный email или пароль.", "danger")

    return render_template("login.html", form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        new_user = User(name=form.name.data, email=form.email.data, password_hash=hashed_password)
        try:
            db.session.add(new_user)
            db.session.commit()
            flash("Регистрация успешна!", "success")
            return redirect(url_for('questionary', id=new_user.id))
        except Exception as e:
            db.session.rollback()
            flash("Ошибка регистрации: " + str(e), "danger")
    return render_template("register.html", form=form)


@app.route('/forgot_pass', methods=['GET', 'POST'])
def forgot_pass():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            # Удаляем старые токены
            PasswordResetToken.query.filter_by(user_id=user.id).delete()

            # Создаем новый токен
            token = secrets.token_urlsafe(32)
            expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
            reset_token = PasswordResetToken(
                user_id=user.id,
                token=token,
                expires_at=expires_at
            )
            db.session.add(reset_token)
            db.session.commit()

            # Отправляем email
            reset_url = url_for('reset_password', token=token, _external=True)
            # print(f"[DEBUG] Password reset link: {reset_url}")
            msg = Message('Восстановление пароля',
                          sender='noreply@yourdomain.com',
                          recipients=[user.email])
            msg.body = f'''Для восстановления пароля перейдите по ссылке:
    {reset_url}

    Ссылка действительна в течение 1 часа.
    '''
            mail.send(msg)

        flash('Если email зарегистрирован, на него отправлена инструкция', 'info')
        return redirect(url_for('login'))

    return render_template('forgot_pass.html', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    reset_token = PasswordResetToken.query.filter_by(token=token).first()

    if not reset_token or reset_token.expires_at < datetime.now(timezone.utc):
        flash('Ссылка недействительна или срок ее действия истек', 'danger')
        return redirect(url_for('forgot_pass'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.get(reset_token.user_id)
        user.password_hash = generate_password_hash(form.password.data)

        # Удаляем использованный токен
        db.session.delete(reset_token)
        db.session.commit()

        flash('Пароль успешно изменен. Теперь вы можете войти.', 'success')
        return redirect(url_for('login'))

    return render_template('reset_password.html', form=form)


@app.route('/questionary', methods=['GET', 'POST'])
def questionary():
    return redirect(url_for('questionary'))


@app.route('/basepage')
def basepage():
    return render_template('basepage.html')

@app.route('/like/<int:liked_user_id>', methods=['POST'])
def like_user(liked_user_id):
    if 'user_id' not in session:
        flash("Сначала войдите в аккаунт", "warning")
        return redirect(url_for('login'))

    user_id = session['user_id']
    if user_id == liked_user_id:
        flash("Нельзя лайкнуть себя :)", "info")
        return redirect(request.referrer or url_for('basepage'))

    existing_like = Like.query.filter_by(user_id=user_id, liked_user_id=liked_user_id).first()
    if existing_like:
        db.session.delete(existing_like)
        db.session.commit()
        flash("Лайк удалён", "info")
    else:
        new_like = Like(user_id=user_id, liked_user_id=liked_user_id)
        db.session.add(new_like)
        db.session.commit()
        flash("Вы поставили лайк!", "success")

    return redirect(request.referrer or url_for('basepage'))


@app.route('/likes')
def likes_page():
    if 'user_id' not in session:
        flash("Сначала войдите в аккаунт", "warning")
        return redirect(url_for('login'))

    user_id = session['user_id']

    # Лайки, которые я поставил
    liked_users = User.query.join(Like, User.id == Like.liked_user_id)\
        .filter(Like.user_id == user_id).all()

    # Лайки, которые получил
    users_who_liked_me = User.query.join(Like, User.id == Like.user_id)\
        .filter(Like.liked_user_id == user_id).all()

    # Взаимные лайки (матчи)
    matches = [u for u in liked_users if u in users_who_liked_me]

    return render_template(
        "likes.html",
        liked_users=liked_users,
        users_who_liked_me=users_who_liked_me,
        matches=matches
    )

@app.route('/user_profile/<int:id>', methods=['GET', 'POST'])
def user_profile():
    return render_template('user_profile.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
