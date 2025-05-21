import os
import secrets
from datetime import timezone
import logging

from flask import Flask, render_template, redirect, url_for, flash, session, request, jsonify
from flask_mail import Message, Mail
from flask_wtf import CSRFProtect
from sqlalchemy import or_
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from config import Connect
from forms import RegisterForm, LoginForm, ForgotPasswordForm, ResetPasswordForm, QuestionnaireForm
from models import db, User, PasswordResetToken, Like, Messages, Questionnaire, Matches
from toxic_filter import is_offensive


logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Connect)
db.init_app(app)
csrf = CSRFProtect(app)
app.config['MAIL_SERVER'] = 'smtp.yourmailserver.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@example.com'
app.config['MAIL_PASSWORD'] = 'your-email-password'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
mail = Mail(app)



@app.route('/')
def index():
    return render_template('index.html')


from datetime import datetime, timedelta

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if 'login_attempts' not in session:
        session['login_attempts'] = 0
        session['block_until'] = None

    if session.get('block_until'):
        block_until = datetime.fromisoformat(session['block_until'])
        if datetime.now(timezone.utc) < block_until:
            if request.is_json:
                return jsonify({"success": False, "message": "Слишком много попыток. Попробуйте через 5 минут."}), 429
            else:
                flash('Слишком много попыток входа. Попробуйте через 5 минут.', 'danger')
                return render_template('login.html', form=form)
        else:
            session['login_attempts'] = 0
            session['block_until'] = None

    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')

            user = User.query.filter_by(email=email).first()
            if user and check_password_hash(user.password_hash, password):
                session["user_id"] = user.id
                session['login_attempts'] = 0
                flash("Вход выполнен успешно!", "success")
                return jsonify({"success": True}), 200
            else:
                session['login_attempts'] += 1
                if session['login_attempts'] >= 5:
                    block_time = datetime.now(timezone.utc) + timedelta(minutes=5)
                    session['block_until'] = block_time.isoformat()
                    return jsonify({"success": False, "message": "Слишком много попыток. Блокировка на 5 минут."}), 429
                return jsonify({"success": False, "message": "Неверный email или пароль."}), 400

        else:
            if form.validate_on_submit():
                user = User.query.filter_by(email=form.email.data).first()
                if user and check_password_hash(user.password_hash, form.password.data):
                    session["user_id"] = user.id
                    session['login_attempts'] = 0
                    flash("Вход выполнен успешно!", "success")
                    return redirect(url_for("basepage"))
                else:
                    session['login_attempts'] += 1
                    if session['login_attempts'] >= 5:
                        block_time = datetime.now(timezone.utc) + timedelta(minutes=5)
                        session['block_until'] = block_time.isoformat()
                        flash('Слишком много попыток входа. Блокировка на 5 минут.', 'danger')
                    else:
                        flash('Неверный email или пароль.', 'danger')

    return render_template("login.html", form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if request.method == 'POST':
        # Обработка JSON-запроса (через fetch)
        if request.is_json:
            data = request.get_json()
            name = data.get('name')
            email = data.get('email')
            password = data.get('password')

            if not name or not email or not password:
                return jsonify({"success": False, "message": "Заполните все поля."}), 400

            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                return jsonify({"success": False, "message": "Этот email уже зарегистрирован."}), 400

            hashed_password = generate_password_hash(password)
            new_user = User(name=name, email=email, password_hash=hashed_password)

            try:
                db.session.add(new_user)
                db.session.commit()

                session['user_id'] = new_user.id
                return jsonify({"success": True}), 200
            except Exception as err:
                db.session.rollback()
                logger.error(f"[REGISTER ERROR][JSON]: {err}")
                return jsonify({"success": False, "message": "Ошибка сервера. Попробуйте позже."}), 500

        # Обработка обычной формы (HTML submit)
        elif form.validate_on_submit():
            hashed_password = generate_password_hash(form.password.data)
            new_user = User(name=form.name.data, email=form.email.data, password_hash=hashed_password)

            try:
                db.session.add(new_user)
                db.session.commit()

                session['user_id'] = new_user.id
                flash("Регистрация успешна!", "success")
                return redirect(url_for('questionary'))
            except Exception as err:
                db.session.rollback()
                logger.error(f"[REGISTER ERROR][FORM]: {err}")
                flash("Ошибка регистрации. Попробуйте позже.", "danger")

    return render_template("register.html", form=form)


@app.route('/forgot_pass', methods=['GET', 'POST'])
def forgot_pass():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            # Удаляем старые токены
            PasswordResetToken.query.filter_by(user_id=user.id).delete()

            # Создаём новый токен
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
        flash('Ссылка недействительна или срок её действия истек', 'danger')
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



# @app.route('/test_reset_password')
# def test_reset_password():
#     from forms import ResetPasswordForm
#     form = ResetPasswordForm()
#     return render_template('reset_password.html', form=form)


@app.route('/questionary', methods=['GET', 'POST'])
def questionary():
    if 'user_id' not in session:
        return redirect(url_for('register'))

    user_id = session['user_id']
    form = QuestionnaireForm()

    if form.validate_on_submit():
        profile_photo_path = None
        additional_photos_paths = []

        # Сохранение фото профиля
        if form.profile_photo.data:
            filename = secure_filename(form.profile_photo.data.filename)
            profile_photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            form.profile_photo.data.save(profile_photo_path)

        # Сохранение дополнительных фото
        if form.additional_photos.data:
            for file in form.additional_photos.data:
                if file.filename:
                    fname = secure_filename(file.filename)
                    full_path = os.path.join(app.config['UPLOAD_FOLDER'], fname)
                    file.save(full_path)
                    additional_photos_paths.append(full_path)

        questionnaire = Questionnaire(
            age=form.age.data,
            gender=form.gender.data,
            country=form.country.data,
            city=form.city.data,
            height=form.height.data,
            zodiac_sign=form.zodiac_sign.data,
            interests=form.interests.data,
            description=form.description.data,
            profile_photo=profile_photo_path,
            additional_photos=additional_photos_paths,
            user_id=user_id
        )

        db.session.add(questionnaire)
        db.session.commit()

        return redirect(url_for('basepage'))

    return render_template('questionary.html', form=form)


@app.route('/basepage')
def basepage():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    matched_ids = get_matched_user_ids(user_id)

    query = Questionnaire.query.filter(
        Questionnaire.user_id != user_id,
        ~Questionnaire.user_id.in_(matched_ids)
    )

    # Поисковый запрос
    keyword = request.args.get('query', '').strip().lower()
    if keyword:
        query = query.filter(
            or_(
                Questionnaire.interests.ilike(f'%{keyword}%'),
                Questionnaire.description.ilike(f'%{keyword}%'),
                Questionnaire.city.ilike(f'%{keyword}%')
            )
        )

    # Пол (gender)
    gender = request.args.get('gender')
    if gender:
        query = query.filter_by(gender=gender)

    # Возраст
    age_from = request.args.get('ageFrom', type=int)
    age_to = request.args.get('ageTo', type=int)
    if age_from:
        query = query.filter(Questionnaire.age >= age_from)
    if age_to:
        query = query.filter(Questionnaire.age <= age_to)

    # Страна и город
    country = request.args.get('country', '').strip()
    if country:
        query = query.filter(Questionnaire.country.ilike(f'%{country}%'))

    city = request.args.get('city', '').strip()
    if city:
        query = query.filter(Questionnaire.city.ilike(f'%{city}%'))

    # Рост
    height_from = request.args.get('heightFrom', type=int)
    height_to = request.args.get('heightTo', type=int)
    if height_from:
        query = query.filter(Questionnaire.height >= height_from)
    if height_to:
        query = query.filter(Questionnaire.height <= height_to)

    # Знак зодиака
    zodiac = request.args.get('zodiac_sign', '').strip()
    if zodiac:
        query = query.filter(Questionnaire.zodiac_sign.ilike(f'%{zodiac}%'))

    # Интересы
    interests = request.args.get('interests', '').strip()
    if interests:
        query = query.filter(Questionnaire.interests.ilike(f'%{interests}%'))

    profiles = query.all()
    return render_template('basepage.html', profiles=profiles)


@app.route('/basepage_data')
def basepage_data():
    if 'user_id' not in session:
        return jsonify([])

    user_id = session['user_id']
    matched_ids = get_matched_user_ids(user_id)

    query = Questionnaire.query.filter(
        Questionnaire.user_id != user_id,
        ~Questionnaire.user_id.in_(matched_ids)
    )

    # Поиск по слову
    keyword = request.args.get('query', '').strip().lower()
    if keyword:
        query = query.filter(
            or_(
                Questionnaire.interests.ilike(f'%{keyword}%'),
                Questionnaire.description.ilike(f'%{keyword}%'),
                Questionnaire.city.ilike(f'%{keyword}%')
            )
        )

    # Фильтры
    gender = request.args.get('gender')
    if gender:
        query = query.filter_by(gender=gender)

    age_from = request.args.get('ageFrom', type=int)
    age_to = request.args.get('ageTo', type=int)
    if age_from:
        query = query.filter(Questionnaire.age >= age_from)
    if age_to:
        query = query.filter(Questionnaire.age <= age_to)

    country = request.args.get('country', '').strip()
    if country:
        query = query.filter(Questionnaire.country.ilike(f'%{country}%'))

    city = request.args.get('city', '').strip()
    if city:
        query = query.filter(Questionnaire.city.ilike(f'%{city}%'))

    height_from = request.args.get('heightFrom', type=int)
    height_to = request.args.get('heightTo', type=int)
    if height_from:
        query = query.filter(Questionnaire.height >= height_from)
    if height_to:
        query = query.filter(Questionnaire.height <= height_to)

    zodiac = request.args.get('zodiac_sign', '').strip()
    if zodiac:
        query = query.filter(Questionnaire.zodiac_sign.ilike(f'%{zodiac}%'))

    interests = request.args.get('interests', '').strip()
    if interests:
        query = query.filter(Questionnaire.interests.ilike(f'%{interests}%'))

    # Пагинация
    page = request.args.get('page', 1, type=int)
    per_page = 10
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    results = []

    for profile in paginated.items:
        results.append({
            "id": profile.id,
            "name": profile.user.name,
            "age": profile.age,
            "city": profile.city,
            "country": profile.country,
            "zodiac_sign": profile.zodiac_sign,
            "profile_photo": profile.profile_photo
        })


@app.route('/api/unread_counts')
def unread_counts():
    if 'user_id' not in session:
        return jsonify({'likes': 0, 'messages': 0})

    user_id = session['user_id']

    new_likes = Like.query.filter_by(liked_user_id=user_id, is_new=True).count()
    new_messages = Messages.query.filter_by(receiver_id=user_id, is_read=False).count()

    return jsonify({'likes': new_likes, 'messages': new_messages})




@app.route('/like/<int:liked_user_id>', methods=['POST'])
def like_user(liked_user_id):
    if 'user_id' not in session:
        if request.is_json:
            return jsonify({"success": False, "message": "Требуется авторизация"}), 401
        flash("Сначала войдите в аккаунт", "warning")
        return redirect(url_for('login'))

    user_id = session['user_id']

    if user_id == liked_user_id:
        if request.is_json:
            return jsonify({"success": False, "message": "Нельзя лайкнуть себя"}), 400
        flash("Нельзя лайкнуть себя :)", "info")
        return redirect(request.referrer or url_for('basepage'))

    from models import Matches

    existing_like = Like.query.filter_by(user_id=user_id, liked_user_id=liked_user_id).first()

    if existing_like:
        db.session.delete(existing_like)

        # Удаляем матч, если он был
        match = Matches.query.filter(
            ((Matches.user_one_id == user_id) & (Matches.user_two_id == liked_user_id)) |
            ((Matches.user_one_id == liked_user_id) & (Matches.user_two_id == user_id))
        ).first()
        if match:
            db.session.delete(match)

        db.session.commit()
        if request.is_json:
            return jsonify({"success": True, "message": "Лайк удалён"})
        flash("Лайк удалён", "info")

    else:
        new_like = Like(user_id=user_id, liked_user_id=liked_user_id, is_new=True)
        db.session.add(new_like)

        reciprocal_like = Like.query.filter_by(user_id=liked_user_id, liked_user_id=user_id).first()

        if reciprocal_like:
            existing_match = Matches.query.filter(
                ((Matches.user_one_id == user_id) & (Matches.user_two_id == liked_user_id)) |
                ((Matches.user_one_id == liked_user_id) & (Matches.user_two_id == user_id))
            ).first()

            if not existing_match:
                match = Matches(
                    user_one_id=user_id,
                    user_two_id=liked_user_id,
                    matched_ad="взаимный лайк"
                )
                db.session.add(match)

        db.session.commit()
        if request.is_json:
            return jsonify({"success": True, "message": "Лайк поставлен"})
        flash("Вы поставили лайк!", "success")

    return redirect(request.referrer or url_for('basepage'))




@app.route('/likes')
def likes_page():
    if 'user_id' not in session:
        flash("Сначала войдите в аккаунт", "warning")
        return redirect(url_for('login'))

    user_id = session['user_id']

    liked_users = User.query.join(Like, User.id == Like.liked_user_id)\
        .filter(Like.user_id == user_id).all()

    users_who_liked_me = User.query.join(Like, User.id == Like.user_id)\
        .filter(Like.liked_user_id == user_id).all()

    matched_ids = get_matched_user_ids(user_id)
    matches = User.query.filter(User.id.in_(matched_ids)).all()

    # Сброс флага новых лайков
    Like.query.filter_by(liked_user_id=user_id, is_new=True).update({'is_new': False})
    db.session.commit()

    return render_template(
        "likes.html",
        liked_users=liked_users,
        users_who_liked_me=users_who_liked_me,
        matches=matches
    )



@app.route('/chats')
def chats():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    current_user_id = session['user_id']

    sent = db.session.query(Messages.receiver_id.label('partner_id')).filter(Messages.sender_id == current_user_id)
    received = db.session.query(Messages.sender_id.label('partner_id')).filter(Messages.receiver_id == current_user_id)
    union_query = sent.union(received).subquery()

    users = db.session.query(User).join(union_query, User.id == union_query.c.partner_id).all()

    for user in users:
        last_msg = Messages.query.filter(
            ((Messages.sender_id == current_user_id) & (Messages.receiver_id == user.id)) |
            ((Messages.sender_id == user.id) & (Messages.receiver_id == current_user_id))
        ).order_by(Messages.created_at.desc()).first()

        if last_msg:
            user.last_message = last_msg.message
            user.last_message_time = last_msg.created_at
        else:
            user.last_message = "Нет сообщений"
            user.last_message_time = None

    return render_template("chats.html", chat_partners=users)


@app.route("/chat/<int:user_id>")
def chat(user_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    current_user_id = session['user_id']

    unread_messages = Messages.query.filter_by(sender_id=user_id, receiver_id=current_user_id, is_read=False).all()
    for msg in unread_messages:
        msg.is_read = True
    db.session.commit()

    other_user = db.session.get(User, user_id)  # <-- получаем пользователя
    return render_template("chat.html", other_user=other_user)  # <-- передаём его сюда


@csrf.exempt
@app.route("/send_message", methods=["POST"])
def send_message():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    # print("DEBUG: request.form =", request.form)

    sender_id = session["user_id"]
    receiver_id = request.form.get("receiver_id", type=int)
    content = request.form.get("message", "").strip()

    # print("DEBUG: receiver_id =", receiver_id)
    # print("DEBUG: content =", content)

    if not receiver_id or not content:
        return jsonify({"error": "Сообщение содержит недопустимый контент"}), 400

    # Проверка на взаимный лайк
    match1 = Like.query.filter_by(user_id=sender_id, liked_user_id=receiver_id).first()
    match2 = Like.query.filter_by(user_id=receiver_id, liked_user_id=sender_id).first()

    if not (match1 and match2):
        return jsonify({"error": "Можно писать сообщения только при взаимной симпатии."}), 403

    # Фильтрация токсичности
    if is_offensive(content):
        return jsonify({"error": "Сообщение содержит недопустимый контент."}), 400

    msg = Messages(
        sender_id=sender_id,
        receiver_id=receiver_id,
        message=content,
        created_at=datetime.now(timezone.utc)
    )
    db.session.add(msg)
    db.session.commit()

    return jsonify({"success": True})



@app.route("/chat_updates/<int:user_id>")
def chat_updates(user_id):
    if "user_id" not in session:
        return jsonify({"error": "unauthorized"}), 401

    current_user_id = session["user_id"]

    messages = Messages.query.filter(
        ((Messages.sender_id == current_user_id) & (Messages.receiver_id == user_id)) |
        ((Messages.sender_id == user_id) & (Messages.receiver_id == current_user_id))
    ).order_by(Messages.created_at).all()

    return jsonify([
        {
            "id": m.message_id,
            "text": m.message,
            "sender_id": m.sender_id,
            "created_at": m.created_at.strftime('%H:%M %d.%m.%Y'),
            "is_read": m.is_read
        } for m in messages
    ])


@app.before_request
def update_last_seen():
    if 'user_id' in session:
        user = db.session.get(User, session['user_id'])  # ← вот тут
        if user:
            user.last_seen = datetime.now(timezone.utc)
            db.session.commit()


def is_online(user):
    if user.last_seen:
        return datetime.now(timezone.utc) - user.last_seen < timedelta(minutes=5)
    return False

app.jinja_env.globals['is_online'] = is_online


@app.route('/user_profile')
def user_profile():
    return render_template('user_profile.html')



@app.route('/view_profile/<int:id>')
def view_profile(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    current_user_id = session['user_id']
    profile = Questionnaire.query.get_or_404(id)

    # Проверка взаимного лайка
    like_from_me = Like.query.filter_by(user_id=current_user_id, liked_user_id=profile.user_id).first()
    like_from_them = Like.query.filter_by(user_id=profile.user_id, liked_user_id=current_user_id).first()
    mutual_like = like_from_me and like_from_them

    return render_template('view_profile.html', profile=profile, mutual_like=mutual_like)


@app.route('/block/<int:user_id>', methods=['POST'])
def block_user(user_id):
    if 'user_id' not in session:
        flash("Сначала войдите в аккаунт", "warning")
        return redirect(url_for('login'))

    current_user_id = session['user_id']

    like = Like.query.filter_by(user_id=current_user_id, liked_user_id=user_id).first()

    if like:
        like.is_blocked = True
    else:
        like = Like(user_id=current_user_id, liked_user_id=user_id, is_blocked=True)
        db.session.add(like)

    db.session.commit()
    flash("Пользователь заблокирован.", "info")
    return redirect(url_for('view_profile', id=user_id))


@app.route('/unblock/<int:user_id>', methods=['POST'])
def unblock_user(user_id):
    if 'user_id' not in session:
        flash("Сначала войдите в аккаунт", "warning")
        return redirect(url_for('login'))

    current_user_id = session['user_id']

    like = Like.query.filter_by(user_id=current_user_id, liked_user_id=user_id).first()

    if like and like.is_blocked:
        like.is_blocked = False
        db.session.commit()
        flash("Пользователь разблокирован.", "info")
    else:
        flash("Этот пользователь не был заблокирован.", "warning")

    return redirect(url_for('user_profile'))




def get_matched_user_ids(user_id):
    match_pairs = db.session.query(Matches.user_one_id, Matches.user_two_id).filter(
        (Matches.user_one_id == user_id) | (Matches.user_two_id == user_id)
    ).all()

    matched_ids = set()
    for u1, u2 in match_pairs:
        matched_ids.update([u1, u2])
    matched_ids.discard(user_id)

    return matched_ids


def build_filtered_profiles_query(user_id):
    matched_ids = get_matched_user_ids(user_id)

    query = Questionnaire.query.filter(
        Questionnaire.user_id != user_id,
        ~Questionnaire.user_id.in_(matched_ids)
    )

    keyword = request.args.get('query', '').strip().lower()
    if keyword:
        query = query.filter(
            or_(
                Questionnaire.interests.ilike(f'%{keyword}%'),
                Questionnaire.description.ilike(f'%{keyword}%'),
                Questionnaire.city.ilike(f'%{keyword}%')
            )
        )

    gender = request.args.get('gender')
    if gender:
        query = query.filter_by(gender=gender)

    age_from = request.args.get('ageFrom', type=int)
    age_to = request.args.get('ageTo', type=int)
    if age_from:
        query = query.filter(Questionnaire.age >= age_from)
    if age_to:
        query = query.filter(Questionnaire.age <= age_to)

    country = request.args.get('country', '').strip()
    if country:
        query = query.filter(Questionnaire.country.ilike(f'%{country}%'))

    city = request.args.get('city', '').strip()
    if city:
        query = query.filter(Questionnaire.city.ilike(f'%{city}%'))

    height_from = request.args.get('heightFrom', type=int)
    height_to = request.args.get('heightTo', type=int)
    if height_from:
        query = query.filter(Questionnaire.height >= height_from)
    if height_to:
        query = query.filter(Questionnaire.height <= height_to)

    zodiac = request.args.get('zodiac_sign', '').strip()
    if zodiac:
        query = query.filter(Questionnaire.zodiac_sign.ilike(f'%{zodiac}%'))

    interests = request.args.get('interests', '').strip()
    if interests:
        query = query.filter(Questionnaire.interests.ilike(f'%{interests}%'))

    return query


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

