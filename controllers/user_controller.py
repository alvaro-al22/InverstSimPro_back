import re
import random
import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_bcrypt import Bcrypt
import jwt
from models import db, User

user_bp = Blueprint('user', __name__)
bcrypt = Bcrypt()

# Diccionario para almacenar verificaciones pendientes (para registro con verificación de correo)
pending_verifications = {}

def is_valid_password(password):
    # Requiere: mínimo 8 caracteres, al menos una minúscula, una mayúscula, un dígito y un carácter especial.
    pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
    return re.match(pattern, password)

@user_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({"error": "Faltan datos"}), 400

    if not is_valid_password(password):
        return jsonify({
            "error": "La contraseña debe tener al menos 8 caracteres, incluir mayúsculas, minúsculas, números y un carácter especial."
        }), 400

    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({"error": "El usuario ya existe"}), 400

    # Generar código de verificación (6 dígitos)
    verification_code = str(random.randint(100000, 999999))
    pending_verifications[email] = {
        "username": username,
        "password": password,
        "code": verification_code,
        "timestamp": datetime.datetime.utcnow()
    }

    # En producción, aquí se enviaría un correo con el código. Para la demo se imprime.
    print(f"Enviando correo a {email} con código de verificación: {verification_code}")

    return jsonify({"message": "Se ha enviado un código de verificación a tu correo."}), 200

@user_bp.route('/verify', methods=['POST'])
def verify():
    data = request.get_json()
    email = data.get('email')
    code = data.get('code')

    if email not in pending_verifications:
        return jsonify({"error": "No se encontró una verificación pendiente para ese correo."}), 400

    pending = pending_verifications[email]
    if pending["code"] != code:
        return jsonify({"error": "Código de verificación incorrecto."}), 400

    password_hash = bcrypt.generate_password_hash(pending["password"]).decode('utf-8')
    new_user = User(username=pending["username"], email=email, password_hash=password_hash)
    db.session.add(new_user)
    db.session.commit()

    del pending_verifications[email]

    return jsonify({"message": "Usuario registrado exitosamente."}), 201

@user_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Faltan datos"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        return jsonify({"error": "Credenciales inválidas"}), 401

    # Generar token de acceso (vigente 15 minutos)
    access_token = jwt.encode({
        "user_id": user.id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    }, current_app.config['SECRET_KEY'], algorithm="HS256")
    
    # Generar token de refresco (vigente 7 días)
    refresh_token = jwt.encode({
        "user_id": user.id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }, current_app.config['SECRET_KEY'], algorithm="HS256")

    # Se incluye el nombre de usuario en la respuesta
    return jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "username": user.username
    }), 200


@user_bp.route('/refresh', methods=['POST'])
def refresh():
    data = request.get_json()
    refresh_token = data.get('refresh_token')
    if not refresh_token:
        return jsonify({"error": "Se requiere el refresh token"}), 400

    try:
        decoded = jwt.decode(refresh_token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
        user_id = decoded.get("user_id")
        # Emitir un nuevo token de acceso
        new_access_token = jwt.encode({
            "user_id": user_id,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
        }, current_app.config['SECRET_KEY'], algorithm="HS256")
        return jsonify({"access_token": new_access_token}), 200
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "El refresh token ha expirado."}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Refresh token inválido."}), 401
