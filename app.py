from flask import Flask, render_template, url_for

app = Flask(__name__)


@app.route('/')
def index():
    print(url_for('index'))
    return render_template('index.html')


@app.route('/login')
def login():
    print(url_for('login'))
    return render_template('login.html')


@app.route('/register')
def register():
    print(url_for('register'))
    return render_template('register.html')


@app.route('/forgot_pass')
def forgot_pass():
    print(url_for('forgot_pass'))
    return render_template('forgot_pass.html')


@app.route('/questionary')
def questionary():
    print(url_for('questionary'))
    return render_template('questionary.html')


if __name__ == '__main__':
    app.run()
