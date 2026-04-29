from flask import Blueprint, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import os
from datetime import datetime, timedelta, timezone
from functools import wraps

db = SQLAlchemy()
auth_bp = Blueprint('auth', __name__)


class User(db.Model):
    __tablename__ = 'users'
    nim      = db.Column(db.String(15), primary_key=True)
    nama     = db.Column(db.String(100), nullable=False)
    email    = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)
    role     = db.Column(db.String(10), nullable=False, server_default='mahasiswa')


def _get_secret():
    return os.getenv('SECRET_KEY', 'dev-secret-key')


def create_token(nim: str) -> str:
    payload = {
        'nim': nim,
        'exp': datetime.now(timezone.utc) + timedelta(days=7),
        'iat': datetime.now(timezone.utc),
    }
    return jwt.encode(payload, _get_secret(), algorithm='HS256')


def get_nim_from_token() -> str | None:
    """Ambil NIM dari Authorization: Bearer <token>. Return None jika tidak valid."""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    token = auth_header.split(' ', 1)[1]
    try:
        payload = jwt.decode(token, _get_secret(), algorithms=['HS256'])
        return payload.get('nim')
    except Exception:
        return None


def token_required(f):
    """Decorator: pastikan request punya JWT valid, inject user sebagai arg pertama."""
    @wraps(f)
    def decorated(*args, **kwargs):
        nim = get_nim_from_token()
        if not nim:
            return jsonify({'error': 'Token tidak ditemukan atau tidak valid'}), 401
        user = User.query.get(nim)
        if not user:
            return jsonify({'error': 'User tidak ditemukan'}), 404
        return f(user, *args, **kwargs)
    return decorated


# ── REGISTER ──────────────────────────────────────────────────

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Request body tidak valid'}), 400

    required_fields = ['nim', 'nama', 'email', 'password']
    missing = [f for f in required_fields if not data.get(f, '').strip()]
    if missing:
        return jsonify({'error': f"Field berikut wajib diisi: {', '.join(missing)}"}), 400

    if User.query.get(data['nim'].strip()):
        return jsonify({'error': 'NIM sudah terdaftar'}), 400

    if User.query.filter_by(email=data['email'].strip()).first():
        return jsonify({'error': 'Email sudah terdaftar'}), 400

    try:
        new_user = User(
            nim=data['nim'].strip(),
            nama=data['nama'].strip(),
            email=data['email'].strip(),
            password=generate_password_hash(data['password']),
        )
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'Registrasi berhasil'}), 201
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Terjadi kesalahan server, coba lagi'}), 500


# ── LOGIN ──────────────────────────────────────────────────────

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Request body tidak valid'}), 400

    if not data.get('nim') or not data.get('password'):
        return jsonify({'error': 'NIM dan password wajib diisi'}), 400

    user = User.query.get(data['nim'].strip())
    if not user or not check_password_hash(user.password, data['password']):
        return jsonify({'error': 'NIM atau password salah'}), 401

    token = create_token(user.nim)
    return jsonify({
        'message': 'Login sukses',
        'token': token,
        'user': {'nim': user.nim, 'nama': user.nama, 'role': user.role},
    }), 200


# ── ME ─────────────────────────────────────────────────────────

@auth_bp.route('/me', methods=['GET'])
@token_required
def get_me(user):
    return jsonify({'nim': user.nim, 'nama': user.nama, 'role': user.role}), 200


# ── LOGOUT ─────────────────────────────────────────────────────

@auth_bp.route('/logout', methods=['POST'])
def logout():
    return jsonify({'message': 'Logged out'}), 200
