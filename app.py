# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from flask_bcrypt import Bcrypt
import re
import os
import uuid
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY", "dev-secret")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///users.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = os.path.join("static", "uploads", "profiles")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5MB max file size

# Ensure upload directory exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    profile_picture = db.Column(db.String(200), nullable=True, default='media/default-avatar.png')

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        self.last_login = datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        db.session.commit()

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

# ----------- ACCOUNT API ROUTES -----------

@app.route('/api/account/upload-avatar', methods=['POST'])
@login_required
def upload_avatar():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "Nessun file selezionato"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "Nessun file selezionato"}), 400
    
    if file and allowed_file(file.filename):
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        try:
            file.save(filepath)
            
            # Update user profile picture path
            old_picture = current_user.profile_picture
            current_user.profile_picture = f"uploads/profiles/{unique_filename}"
            db.session.commit()
            
            # Delete old profile picture if it's not the default
            if old_picture and old_picture != 'media/default-avatar.png' and os.path.exists(os.path.join("static", old_picture)):
                try:
                    os.remove(os.path.join("static", old_picture))
                except:
                    pass  # Don't fail if we can't delete old file
            
            return jsonify({
                "success": True, 
                "profile_picture": current_user.profile_picture
            })
        except Exception as e:
            return jsonify({"success": False, "error": "Errore durante il caricamento"}), 500
    
    return jsonify({"success": False, "error": "Formato file non supportato"}), 400

@app.route('/api/account/edit-profile', methods=['POST'])
@login_required
def edit_profile():
    name = request.form.get('name', '').strip()
    
    if not name:
        return jsonify({"success": False, "error": "Il nome è obbligatorio"}), 400
    
    # Validate name format
    if not re.match(r"^[\w\sàèéìòùÀÈÉÌÒÙ''\-]{2,40}$", name):
        return jsonify({"success": False, "error": "Il nome contiene caratteri non validi"}), 400
    
    try:
        current_user.name = name
        db.session.commit()
        return jsonify({"success": True, "name": current_user.name})
    except Exception as e:
        return jsonify({"success": False, "error": "Errore durante l'aggiornamento"}), 500

@app.route('/api/account/change-password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password', '').strip()
    new_password = request.form.get('new_password', '').strip()
    confirm_password = request.form.get('confirm_password', '').strip()
    
    if not all([current_password, new_password, confirm_password]):
        return jsonify({"success": False, "error": "Tutti i campi sono obbligatori"}), 400
    
    if not current_user.check_password(current_password):
        return jsonify({"success": False, "error": "Password attuale non corretta"}), 400
    
    if new_password != confirm_password:
        return jsonify({"success": False, "error": "Le nuove password non coincidono"}), 400
    
    if len(new_password) < 6:
        return jsonify({"success": False, "error": "La password deve essere di almeno 6 caratteri"}), 400
    
    try:
        current_user.set_password(new_password)
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": "Errore durante l'aggiornamento della password"}), 500

@app.route('/api/account/export-data', methods=['GET'])
@login_required
def export_data():
    try:
        user_data = {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "last_login": current_user.last_login.isoformat() if current_user.last_login else None,
            "profile_picture": current_user.profile_picture,
            "export_date": datetime.now().isoformat()
        }
        
        response = jsonify(user_data)
        response.headers['Content-Disposition'] = f'attachment; filename=orion_account_data_{current_user.id}.json'
        return response
    except Exception as e:
        return jsonify({"success": False, "error": "Errore durante l'esportazione"}), 500

@app.route('/api/account/delete-account', methods=['POST'])
@login_required
def delete_account():
    password = request.form.get('password', '').strip()
    
    if not password:
        return jsonify({"success": False, "error": "Password richiesta per la cancellazione"}), 400
    
    if not current_user.check_password(password):
        return jsonify({"success": False, "error": "Password non corretta"}), 400
    
    try:
        # Delete profile picture if it's not the default
        if current_user.profile_picture and current_user.profile_picture != 'media/default-avatar.png':
            picture_path = os.path.join("static", current_user.profile_picture)
            if os.path.exists(picture_path):
                try:
                    os.remove(picture_path)
                except:
                    pass
        
        # Delete user from database
        db.session.delete(current_user)
        db.session.commit()
        
        # Logout user
        logout_user()
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": "Errore durante la cancellazione dell'account"}), 500


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
        user.update_last_login()
        login_user(user)
        return jsonify({"success": True}), 200
    return jsonify({"success": False, "error": "Credenziali non valide."}), 401

# Run & DB create
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000)
