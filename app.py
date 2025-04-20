from flask import Flask, render_template, redirect, url_for, flash, session
from flask_wtf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegisterForm, LoginForm
from models import db, User
from config import Connect


app = Flask(__name__)
app.config.from_object(Connect)
db.init_app(app)
csrf = CSRFProtect(app)


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
    return render_template('forgot_pass.html')


@app.route('/questionary', methods=['GET', 'POST'])
def questionary():
    return redirect(url_for('questionary'))


@app.route('/basepage')
def basepage():
    return render_template('basepage.html')


@app.route('/user_profile/<int:id>', methods=['GET', 'POST'])
def user_profile():
    return render_template('user_profile.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
