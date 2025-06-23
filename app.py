import os
import secrets
from datetime import timezone
import logging

from flask import Flask, render_template, redirect, url_for, flash, session, request, jsonify
from flask_mail import Message, Mail
from flask_wtf import CSRFProtect
from sqlalchemy import or_, and_
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from config import Connect
from forms import RegisterForm, LoginForm, ForgotPasswordForm, ResetPasswordForm, QuestionnaireForm, ConfirmDeleteForm
from models import db, User, PasswordResetToken, Like, Messages, Questionnaire, Matches, DeletedUserLog
from toxic_filter import is_offensive
from ml_matching import predict_match


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
                    session["just_logged_in"] = True  # вместо flash
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



@app.route('/questionary', methods=['GET', 'POST'])
def questionary():
    if 'user_id' not in session:
        return redirect(url_for('register'))

    user_id = session['user_id']
    form = QuestionnaireForm()

    if form.validate_on_submit():
        profile_photo_path = None
        additional_photo_path = None  # Теперь одно фото

        # Сохранение фото профиля
        if form.profile_photo.data:
            filename = secure_filename(form.profile_photo.data.filename)
            profile_photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            form.profile_photo.data.save(profile_photo_path)

        # Сохранение одного дополнительного фото
        if form.additional_photo.data:
            file = form.additional_photo.data  # Берём только первое
            if file.filename:
                fname = secure_filename(file.filename)
                full_path = os.path.join(app.config['UPLOAD_FOLDER'], fname)
                file.save(full_path)
                additional_photo_path = full_path

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
            additional_photo=additional_photo_path,  # заменено поле
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


    blocked_ids_query = db.session.query(Like.liked_user_id).filter(
        Like.user_id == user_id, Like.is_blocked == True
    ).union(
        db.session.query(Like.user_id).filter(
            Like.liked_user_id == user_id, Like.is_blocked == True
        )
    )
    blocked_ids = [id for (id,) in blocked_ids_query.all()]


    my_questionnaire = Questionnaire.query.filter_by(user_id=user_id).first()
    if not my_questionnaire:
        flash("Сначала создайте анкету.", "warning")
        return redirect(url_for('questionary'))

    def to_dict(q):
        return {
            'age': q.age,
            'gender': q.gender,
            'country': q.country,
            'city': q.city,
            'height': q.height,
            'zodiac_sign': q.zodiac_sign,
            'interests': q.interests
        }

    query = Questionnaire.query.filter(
        Questionnaire.user_id != user_id,
        ~Questionnaire.user_id.in_(matched_ids),
        ~Questionnaire.user_id.in_(blocked_ids)
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

    raw_profiles = query.all()


    my_dict = to_dict(my_questionnaire)
    profiles_with_scores = []
    for q in raw_profiles:
        other_dict = to_dict(q)
        score = predict_match(my_dict, other_dict)
        profiles_with_scores.append((q, score))


    profiles_with_scores.sort(key=lambda tup: tup[1], reverse=True)


    profiles = []
    for q, score in profiles_with_scores:
        q.match_probability = round(score * 100)  # В процентах
        profiles.append(q)

    if session.pop('just_logged_in', False):
        flash("Вход выполнен успешно!", "success")

    return render_template('basepage.html', profiles=profiles)



@app.route('/match_probability/<int:other_user_id>')
def match_probability(other_user_id):
    current_user_id = session.get('user_id')
    if not current_user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    if current_user_id == other_user_id:
        return jsonify({'error': 'Нельзя сравнивать с собой'}), 400

    user1 = Questionnaire.query.filter_by(user_id=current_user_id).first()
    user2 = Questionnaire.query.filter_by(user_id=other_user_id).first()

    if not user1 or not user2:
        return jsonify({'error': 'Анкета не найдена'}), 404

    # Преобразуем в словари с нужными полями
    def to_dict(q):
        return {
            'age': q.age,
            'gender': q.gender,
            'country': q.country,
            'city': q.city,
            'height': q.height,
            'zodiac_sign': q.zodiac_sign,
            'interests': q.interests,
        }

    prob = predict_match(to_dict(user1), to_dict(user2))
    return jsonify({'match_probability': round(prob, 3)})


@app.route('/basepage_data')
def basepage_data():
    if 'user_id' not in session:
        return jsonify([])

    user_id = session['user_id']

    # 🔒 Заблокированные
    blocked_ids_query = db.session.query(Like.liked_user_id).filter(
        Like.user_id == user_id, Like.is_blocked == True
    ).union(
        db.session.query(Like.user_id).filter(
            Like.liked_user_id == user_id, Like.is_blocked == True
        )
    )
    blocked_ids = [id for (id,) in blocked_ids_query.all()]

    # 🔁 Совпавшие
    matched_ids = get_matched_user_ids(user_id)

    # 🔍 Фильтр анкет
    query = Questionnaire.query.filter(
        Questionnaire.user_id != user_id,
        ~Questionnaire.user_id.in_(matched_ids),
        ~Questionnaire.user_id.in_(blocked_ids)
    )

    keyword = request.args.get('query', '').strip().lower()
    if keyword:
        query = query.filter(
            or_(
                Questionnaire.interests.ilike(f'%{keyword}%'),
                Questionnaire.description.ilike(f'%{keyword}%'),
                Questionnaire.city.ilike(f'%{keyword}%'),
                Questionnaire.country.ilike(f'%{keyword}%'),
                Questionnaire.zodiac_sign.ilike(f'%{keyword}%')
            )
        )

    if gender := request.args.get('gender'):
        query = query.filter_by(gender=gender)

    if age_from := request.args.get('ageFrom', type=int):
        query = query.filter(Questionnaire.age >= age_from)
    if age_to := request.args.get('ageTo', type=int):
        query = query.filter(Questionnaire.age <= age_to)

    if country := request.args.get('country', '').strip():
        query = query.filter(Questionnaire.country.ilike(f'%{country}%'))

    if city := request.args.get('city', '').strip():
        query = query.filter(Questionnaire.city.ilike(f'%{city}%'))

    if height_from := request.args.get('heightFrom', type=int):
        query = query.filter(Questionnaire.height >= height_from)
    if height_to := request.args.get('heightTo', type=int):
        query = query.filter(Questionnaire.height <= height_to)

    if zodiac := request.args.get('zodiac_sign', '').strip():
        query = query.filter(Questionnaire.zodiac_sign.ilike(f'%{zodiac}%'))

    if interests := request.args.get('interests', '').strip():
        query = query.filter(Questionnaire.interests.ilike(f'%{interests}%'))

    # 🧠 Мэтчинг
    my_questionnaire = Questionnaire.query.filter_by(user_id=user_id).first()
    def to_dict(q):
        return {
            'age': q.age,
            'gender': q.gender,
            'country': q.country,
            'city': q.city,
            'height': q.height,
            'zodiac_sign': q.zodiac_sign,
            'interests': q.interests
        }

    my_dict = to_dict(my_questionnaire)

    results = []
    for profile in query.all():  # ❗ Без пагинации — загружаем все
        other_dict = to_dict(profile)
        score = predict_match(my_dict, other_dict)
        match_percent = round(score * 100)
        results.append({
            "id": profile.user_id,
            "name": profile.user.name,
            "age": profile.age,
            "city": profile.city,
            "country": profile.country,
            "zodiac_sign": profile.zodiac_sign,
            "profile_photo": profile.profile_photo,
            "match_probability": match_percent
        })

    if not results:
        return jsonify({'empty': True})
    return jsonify({'profiles': results})



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

    # Проверка блокировок
    is_blocked = Like.query.filter(
        ((Like.user_id == user_id) & (Like.liked_user_id == liked_user_id) & (Like.is_blocked == True)) |
        ((Like.user_id == liked_user_id) & (Like.liked_user_id == user_id) & (Like.is_blocked == True))
    ).first()

    if is_blocked:
        if request.is_json:
            return jsonify({"success": False, "message": "Пользователь заблокирован"}), 403
        flash("Пользователь заблокирован.", "warning")
        return redirect(request.referrer or url_for('basepage'))

    existing_like = Like.query.filter_by(user_id=user_id, liked_user_id=liked_user_id).first()

    if existing_like:
        db.session.delete(existing_like)

        match = Matches.query.filter(
            ((Matches.user_one_id == user_id) & (Matches.user_two_id == liked_user_id)) |
            ((Matches.user_one_id == liked_user_id) & (Matches.user_two_id == user_id))
        ).first()
        if match:
            db.session.delete(match)

        db.session.commit()

        if request.is_json:
            return jsonify({"success": True, "message": "Лайк удалён", "match": False})
        flash("Лайк удалён", "info")
        return redirect(request.referrer or url_for('basepage'))

    # Новый лайк
    new_like = Like(user_id=user_id, liked_user_id=liked_user_id, is_new=True)
    db.session.add(new_like)

    reciprocal_like = Like.query.filter_by(user_id=liked_user_id, liked_user_id=user_id).first()
    match_created = False

    if reciprocal_like:
        existing_match = Matches.query.filter(
            ((Matches.user_one_id == user_id) & (Matches.user_two_id == liked_user_id)) |
            ((Matches.user_one_id == liked_user_id) & (Matches.user_two_id == user_id))
        ).first()
        if not existing_match:
            match = Matches(
                user_one_id=min(user_id, liked_user_id),
                user_two_id=max(user_id, liked_user_id),
                matched_ad=datetime.now(timezone.utc)
            )
            db.session.add(match)
            match_created = True

    db.session.commit()

    if request.is_json:
        return jsonify({
            "success": True,
            "message": "Взаимный лайк!" if match_created else "Лайк поставлен",
            "match": match_created
        })

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


    new_likes_exist = Like.query.filter_by(liked_user_id=user_id, is_new=True).count() > 0


    Like.query.filter_by(liked_user_id=user_id, is_new=True).update({'is_new': False})
    db.session.commit()

    return render_template(
        "likes.html",
        liked_users=liked_users,
        users_who_liked_me=users_who_liked_me,
        matches=matches,
        new_likes_exist=new_likes_exist
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

    #Проверка блокировки между пользователями (в обе стороны)
    is_blocked = Like.query.filter(
        ((Like.user_id == current_user_id) & (Like.liked_user_id == user_id) & (Like.is_blocked == True)) |
        ((Like.user_id == user_id) & (Like.liked_user_id == current_user_id) & (Like.is_blocked == True))
    ).first()

    if is_blocked:
        flash("Вы не можете переписываться с этим пользователем.", "danger")
        return redirect(url_for('chats'))

    # Отметить входящие сообщения как прочитанные
    unread_messages = Messages.query.filter_by(sender_id=user_id, receiver_id=current_user_id, is_read=False).all()
    for msg in unread_messages:
        msg.is_read = True
    db.session.commit()

    other_user = db.session.get(User, user_id)
    return render_template("chat.html", other_user=other_user)



@csrf.exempt
@app.route("/send_message", methods=["POST"])
def send_message():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    sender_id = session["user_id"]
    receiver_id = request.form.get("receiver_id", type=int)
    content = request.form.get("message", "").strip()

    if not receiver_id or not content:
        return jsonify({"error": "Сообщение содержит недопустимый контент"}), 400

    #Проверка блокировки (в обе стороны)
    is_blocked = Like.query.filter(
        ((Like.user_id == sender_id) & (Like.liked_user_id == receiver_id) & (Like.is_blocked == True)) |
        ((Like.user_id == receiver_id) & (Like.liked_user_id == sender_id) & (Like.is_blocked == True))
    ).first()

    if is_blocked:
        return jsonify({"error": "Сообщения между вами недоступны."}), 403


    match1 = Like.query.filter_by(user_id=sender_id, liked_user_id=receiver_id).first()
    match2 = Like.query.filter_by(user_id=receiver_id, liked_user_id=sender_id).first()

    if not (match1 and match2):
        return jsonify({"error": "Можно писать сообщения только при взаимной симпатии."}), 403

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


@app.route('/user_profile', methods=['GET', 'POST'])
def user_profile():
    if 'user_id' not in session:
        flash("Сначала войдите в аккаунт", "warning")
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = db.session.get(User, user_id)

    if not user or not user.questionnaire:
        flash("Анкета не найдена", "danger")
        return redirect(url_for('basepage'))

    form = QuestionnaireForm(obj=user.questionnaire)
    delete_form = ConfirmDeleteForm()

    if request.method == 'POST':
        if delete_form.validate_on_submit() and 'submit' in request.form:
            db.session.delete(user)
            db.session.commit()
            session.clear()
            flash("Аккаунт удалён", "info")
            return redirect(url_for("register"))

        if form.validate_on_submit():
            q = user.questionnaire

            if 'age' in request.form:
                q.age = form.age.data

            if 'gender' in request.form:
                q.gender = form.gender.data

            if 'country' in request.form:
                q.country = form.country.data

            if 'city' in request.form:
                q.city = form.city.data

            if 'height' in request.form:
                q.height = form.height.data

            if 'zodiac_sign' in request.form:
                q.zodiac_sign = form.zodiac_sign.data

            if 'interests' in request.form:
                q.interests = form.interests.data

            if 'description' in request.form:
                q.description = form.description.data

            db.session.commit()
            flash("Анкета обновлена", "success")
            return redirect(url_for('user_profile'))

    return render_template("user_profile.html", user=user, form=form, delete_form=delete_form)



@app.route('/blacklist')
def blacklist():
    if 'user_id' not in session:
        flash("Сначала войдите в аккаунт", "warning")
        return redirect(url_for('login'))

    user_id = session['user_id']
    blocked = Like.query.filter_by(user_id=user_id, is_blocked=True).all()
    blocked_user_ids = [like.liked_user_id for like in blocked]
    blocked_users = User.query.filter(User.id.in_(blocked_user_ids)).all()

    return render_template("blacklist.html", blocked_users=blocked_users)


@app.route('/logout')
def logout():
    flash("Вы вышли из аккаунта", "info")
    session.clear()  # очищаем после flash
    return redirect(url_for('login'))



@app.route('/delete_account', methods=['POST'])
def delete_account():
    if 'user_id' not in session:
        flash("Сначала войдите в аккаунт", "warning")
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = db.session.get(User, user_id)

    if not user:
        flash("Пользователь не найден", "danger")
        return redirect(url_for('login'))

    # Логируем удалённого пользователя
    log = DeletedUserLog(
        email=user.email,
        name=user.name,
        deleted_at=datetime.now(timezone.utc)
    )
    db.session.add(log)

    # Удаляем все связанные данные
    Like.query.filter(
        (Like.user_id == user_id) | (Like.liked_user_id == user_id)
    ).delete(synchronize_session=False)

    Messages.query.filter(
        (Messages.sender_id == user_id) | (Messages.receiver_id == user_id)
    ).delete(synchronize_session=False)

    Matches.query.filter(
        (Matches.user_one_id == user_id) | (Matches.user_two_id == user_id)
    ).delete(synchronize_session=False)

    if user.questionnaire:
        db.session.delete(user.questionnaire)

    db.session.delete(user)
    db.session.commit()

    # Полностью очищаем сессию
    session.clear()

    # Сразу направляем на регистрацию и выводим уведомление
    flash("Аккаунт удалён", "info")
    return redirect(url_for('register'))




from flask import request, redirect, url_for, session, render_template, flash

@app.route('/view_profile/<int:id>')
def view_profile(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    current_user_id = session['user_id']
    profile = Questionnaire.query.get_or_404(id)

    # Проверка блокировки (в обе стороны)
    is_blocked = Like.query.filter(
        ((Like.user_id == current_user_id) & (Like.liked_user_id == profile.user_id) & (Like.is_blocked == True)) |
        ((Like.user_id == profile.user_id) & (Like.liked_user_id == current_user_id) & (Like.is_blocked == True))
    ).first()

    if is_blocked:
        flash("Вы не можете просматривать эту анкету.", "warning")
        return redirect(url_for('basepage'))

    # Проверка взаимного лайка
    like_from_me = Like.query.filter_by(user_id=current_user_id, liked_user_id=profile.user_id).first()
    like_from_them = Like.query.filter_by(user_id=profile.user_id, liked_user_id=current_user_id).first()
    mutual_like = like_from_me and like_from_them

    # Новый блок — поддержка return_to (возврат на чат или basepage)
    return_to = request.args.get("return_to", url_for('basepage'))

    return render_template(
        'view_profile.html',
        profile=profile,
        mutual_like=mutual_like,
        return_to=return_to
    )



@app.route('/block/<int:user_id>', methods=['POST'])
def block_user(user_id):
    if 'user_id' not in session:
        if request.is_json:
            return jsonify({"success": False, "message": "Требуется авторизация"}), 401
        flash("Сначала войдите в аккаунт", "warning")
        return redirect(url_for('login'))

    current_user_id = session['user_id']

    # Удаляем совпадение, если есть
    match = Matches.query.filter(
        ((Matches.user_one_id == current_user_id) & (Matches.user_two_id == user_id)) |
        ((Matches.user_one_id == user_id) & (Matches.user_two_id == current_user_id))
    ).first()
    if match:
        db.session.delete(match)

    # Удаляем взаимный лайк от второго пользователя
    reverse_like = Like.query.filter_by(user_id=user_id, liked_user_id=current_user_id).first()
    if reverse_like:
        db.session.delete(reverse_like)

    # Либо обновляем, либо создаём лайк с блокировкой
    like = Like.query.filter_by(user_id=current_user_id, liked_user_id=user_id).first()

    if like:
        like.is_blocked = True
        like.is_new = False
    else:
        like = Like(user_id=current_user_id, liked_user_id=user_id, is_blocked=True, is_new=False)
        db.session.add(like)

    db.session.commit()

    if request.is_json:
        return jsonify({"success": True, "message": "Пользователь заблокирован"})

    flash("Пользователь заблокирован.", "info")
    return redirect(url_for('view_profile', id=user_id))



@app.route('/check_match/<int:other_user_id>')
def check_match(other_user_id):
    if 'user_id' not in session:
        return jsonify({'match': False})

    user_id = session['user_id']
    match = Matches.query.filter_by(user_one_id=user_id, user_two_id=other_user_id).first() \
         or Matches.query.filter_by(user_one_id=other_user_id, user_two_id=user_id).first()

    return jsonify({'match': bool(match)})



@csrf.exempt
@app.route('/unblock/<int:user_id>', methods=['POST'])
def unblock_user(user_id):
    if 'user_id' not in session:
        flash("Сначала войдите в аккаунт", "warning")
        return redirect(url_for('login'))

    current_user_id = session['user_id']

    like = Like.query.filter_by(user_id=current_user_id, liked_user_id=user_id).first()

    if like and like.is_blocked:
        db.session.delete(like)  # полностью удаляем лайк с флагом блокировки
        db.session.commit()
        flash("Пользователь разблокирован", "info")
    else:
        flash("Этот пользователь не был заблокирован.", "warning")

    return redirect(url_for('blacklist'))



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

