"""
from flask import Blueprint, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()
auth_bp = Blueprint('auth', __name__)

class User(db.Model):
    __tablename__ = 'users'
    nim      = db.Column(db.String(15), primary_key=True)
    nama     = db.Column(db.String(100), nullable=False)
    email    = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json(silent=True)

    # Validasi: body harus JSON dan field wajib ada
    if not data:
        return jsonify({"error": "Request body tidak valid"}), 400

    required_fields = ['nim', 'nama', 'email', 'password']
    missing = [f for f in required_fields if not data.get(f, '').strip()]
    if missing:
        return jsonify({"error": f"Field berikut wajib diisi: {', '.join(missing)}"}), 400

    # Validasi: cek duplikat NIM
    if User.query.get(data['nim']):
        return jsonify({"error": "NIM sudah terdaftar"}), 400

    # Validasi: cek duplikat email
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"error": "Email sudah terdaftar"}), 400

    try:
        hashed_pw = generate_password_hash(data['password'])
        new_user = User(
            nim=data['nim'].strip(),
            nama=data['nama'].strip(),
            email=data['email'].strip(),
            password=hashed_pw,
        )
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "Registrasi berhasil"}), 201

    except Exception:
        db.session.rollback()
        return jsonify({"error": "Terjadi kesalahan server, coba lagi"}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True)
    print("DATA MASUK:", data)  # ← tambah ini

    if not data:
        return jsonify({"error": "Request body tidak valid"}), 400

    if not data.get('nim') or not data.get('password'):
        return jsonify({"error": "NIM dan password wajib diisi"}), 400

    user = User.query.get(data['nim'])
    print("USER DITEMUKAN:", user)  # ← tambah ini
    print("NIM DI DB:", user.nim if user else "TIDAK ADA")  # ← tambah ini

    if not user or not check_password_hash(user.password, data['password']):
        return jsonify({"error": "NIM atau password salah"}), 401

    session['user_nim'] = user.nim
    return jsonify({
        "message": "Login sukses",
        "user": {"nim": user.nim, "nama": user.nama},
    }), 200

@auth_bp.route('/me', methods=['GET'])
def get_me():
    nim = session.get('user_nim')
    if not nim:
        return jsonify({"error": "Unauthorized"}), 401

    user = User.query.get(nim)
    if not user:
        # Session ada tapi user sudah dihapus dari DB
        session.pop('user_nim', None)
        return jsonify({"error": "User tidak ditemukan"}), 404

    return jsonify({"nim": user.nim, "nama": user.nama}), 200


@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.pop('user_nim', None)
    return jsonify({"message": "Logged out"}), 200
"""