# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from flask_bcrypt import Bcrypt
import re
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY", "dev-secret")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///users.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/archery')
def archery():
    return render_template('archery.html')

@app.route('/3dprinting')
def printing():
    return render_template('3dprinting.html')

@app.route('/electronics')
def electronics():
    return render_template('electronics.html')

@app.route('/statistics')
@login_required
def statistics():
    return render_template('statistics.html')

@app.route('/booking')
def booking():
    return render_template('booking.html')

@app.route('/shop')
def shop():
    return render_template('shop.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/account')
@login_required
def account():
    return render_template("account.html", user=current_user)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# ----------- API ROUTES -----------

@app.route('/api/auth/signup', methods=['POST'])
def api_signup():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '').strip()

    # Check required fields
    if not name or not email or not password:
        return jsonify({"success": False, "error": "Tutti i campi sono obbligatori."}), 400

    # Validate email format
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        return jsonify({"success": False, "error": "Email non valida."}), 400

    # Optional: validate name format (2–40 chars, letters, accented, space, apostrophe)
    if not re.match(r"^[\w\sàèéìòùÀÈÉÌÒÙ'’\-]{2,40}$", name):
        return jsonify({"success": False, "error": "Il nome contiene caratteri non validi."}), 400

    # Check if user already exists
    if User.query.filter_by(email=email).first():
        return jsonify({"success": False, "error": "Un utente con questa email esiste già."}), 400

    # Create user
    new_user = User(name=name, email=email)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"success": True}), 200

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '').strip()

    user = User.query.filter_by(email=email).first()
    if user and user.check_password(password):
        login_user(user)
        return jsonify({"success": True}), 200
    return jsonify({"success": False, "error": "Credenziali non valide."}), 401

# Run & DB create
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000)
