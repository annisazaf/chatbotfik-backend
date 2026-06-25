from flask import Blueprint, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import os
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone
from functools import wraps

db = SQLAlchemy()
auth_bp = Blueprint("auth", __name__)


class User(db.Model):
    __tablename__ = "users"

    nim = db.Column(db.String(15), primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(10), nullable=False, server_default="mahasiswa")


class PasswordResetToken(db.Model):
    __tablename__ = "password_reset_tokens"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False, index=True)
    token = db.Column(db.String(100), nullable=False, unique=True)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    used = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False,
                           default=lambda: datetime.now(timezone.utc))
    ip_address = db.Column(db.String(45), nullable=True)


def _send_reset_email(to_email: str, reset_url: str) -> None:
    mail_server   = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    mail_port     = int(os.getenv("MAIL_PORT", "587"))
    mail_user     = os.getenv("MAIL_USERNAME", "")
    mail_password = os.getenv("MAIL_PASSWORD", "").replace(" ", "")
    mail_from     = os.getenv("MAIL_FROM", mail_user)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Reset Password – FIKA Konseling Akademik"
    msg["From"]    = mail_from
    msg["To"]      = to_email

    text_body = f"Klik link berikut untuk mereset password kamu (berlaku 1 jam):\n{reset_url}\n\nJika kamu tidak meminta reset password, abaikan email ini."
    html_body = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:auto;padding:32px;background:#f9fafb;border-radius:12px;">
      <h2 style="color:#307045;margin-bottom:8px;">Reset Password ChatbotFIK</h2>
      <p style="color:#374151;margin-bottom:24px;">
        Kamu menerima email ini karena ada permintaan reset password untuk akunmu.<br>
        Link ini hanya berlaku selama <strong>1 jam</strong>.
      </p>
      <a href="{reset_url}"
         style="display:inline-block;background:#307045;color:#fff;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:600;">
        Reset Password
      </a>
      <p style="color:#9ca3af;font-size:12px;margin-top:24px;">
        Jika kamu tidak meminta reset password, abaikan email ini.
      </p>
    </div>"""

    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(mail_server, mail_port, timeout=15) as server:
        server.starttls()
        server.login(mail_user, mail_password)
        server.sendmail(mail_from, to_email, msg.as_string())


def _get_secret():
    return os.getenv("SECRET_KEY", "dev-secret-key")


def create_token(nim: str) -> str:
    payload = {
        "nim": nim,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, _get_secret(), algorithm="HS256")


def get_nim_from_token() -> str | None:
    auth_header = request.headers.get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split(" ", 1)[1]

    try:
        payload = jwt.decode(token, _get_secret(), algorithms=["HS256"])
        return payload.get("nim")
    except Exception:
        return None


def get_nim_from_session_or_token() -> str | None:
    nim = session.get("user_nim")
    if nim:
        return nim

    return get_nim_from_token()


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        nim = get_nim_from_session_or_token()

        if not nim:
            return jsonify({"error": "Token atau session tidak ditemukan / tidak valid"}), 401

        user = User.query.get(nim)

        if not user:
            return jsonify({"error": "User tidak ditemukan"}), 404

        return f(user, *args, **kwargs)

    return decorated


# Lupa password – kirim email reset
@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()

    if not email:
        return jsonify({"error": "Email wajib diisi"}), 400

    ip = request.headers.get("X-Forwarded-For", request.remote_addr or "").split(",")[0].strip()
    window_start = datetime.now(timezone.utc) - timedelta(hours=1)

    # Maks 3 permintaan per email per jam
    email_count = PasswordResetToken.query.filter(
        PasswordResetToken.email == email,
        PasswordResetToken.created_at >= window_start,
    ).count()
    if email_count >= 3:
        return jsonify({"error": "Terlalu banyak permintaan. Coba lagi dalam 1 jam."}), 429

    # Maks 10 permintaan per IP per jam
    if ip:
        ip_count = PasswordResetToken.query.filter(
            PasswordResetToken.ip_address == ip,
            PasswordResetToken.created_at >= window_start,
        ).count()
        if ip_count >= 10:
            return jsonify({"error": "Terlalu banyak permintaan. Coba lagi dalam 1 jam."}), 429

    try:
        user = User.query.filter_by(email=email).first()
    except Exception as exc:
        print(f"[DB ERROR] query user: {exc}")
        return jsonify({"error": "Terjadi kesalahan database. Pastikan backend sudah di-restart."}), 500

    # Selalu kembalikan 200 agar tidak bocor info akun terdaftar atau tidak
    if not user:
        return jsonify({"message": "Jika email terdaftar, link reset telah dikirim"}), 200

    try:
        # Hapus token lama yang belum dipakai
        PasswordResetToken.query.filter_by(email=email, used=False).delete()
        db.session.flush()

        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        db.session.add(PasswordResetToken(
            email=email, token=token, expires_at=expires_at, ip_address=ip or None
        ))
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        print(f"[DB ERROR] simpan token: {exc}")
        return jsonify({"error": "Terjadi kesalahan database. Pastikan backend sudah di-restart."}), 500

    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    reset_url = f"{frontend_url}/reset-password?token={token}"

    try:
        _send_reset_email(email, reset_url)
    except smtplib.SMTPAuthenticationError:
        print("[MAIL ERROR] Autentikasi SMTP gagal. Pastikan App Password Gmail sudah benar.")
        return jsonify({"error": "Gagal mengirim email: autentikasi Gmail gagal. Cek App Password di .env"}), 500
    except smtplib.SMTPException as exc:
        print(f"[MAIL ERROR] SMTP: {exc}")
        return jsonify({"error": "Gagal mengirim email. Cek konfigurasi MAIL_* di .env"}), 500
    except (TimeoutError, OSError) as exc:
        print(f"[MAIL ERROR] Koneksi SMTP timeout: {exc}")
        return jsonify({"error": "Gagal mengirim email: koneksi ke server Gmail timeout. Coba lagi."}), 500
    except Exception as exc:
        print(f"[MAIL ERROR] {exc}")
        return jsonify({"error": "Gagal mengirim email. Cek konfigurasi MAIL_* di .env"}), 500

    return jsonify({"message": "Jika email terdaftar, link reset telah dikirim"}), 200


# Reset password – pakai token dari email
@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json(silent=True) or {}
    token = str(data.get("token", "")).strip()
    new_password = data.get("password", "")

    if not token or not new_password:
        return jsonify({"error": "Token dan password baru wajib diisi"}), 400

    if len(new_password) < 6:
        return jsonify({"error": "Password minimal 6 karakter"}), 400

    record = PasswordResetToken.query.filter_by(token=token, used=False).first()
    if not record:
        return jsonify({"error": "Link reset tidak valid atau sudah digunakan"}), 400

    if record.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        return jsonify({"error": "Link reset sudah kedaluwarsa. Minta ulang reset password"}), 400

    user = User.query.filter_by(email=record.email).first()
    if not user:
        return jsonify({"error": "Akun tidak ditemukan"}), 404

    user.password = generate_password_hash(new_password)
    record.used = True
    db.session.commit()

    return jsonify({"message": "Password berhasil diubah. Silakan login"}), 200


# Daftar/register
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Request body tidak valid"}), 400

    required_fields = ["nim", "nama", "email", "password"]
    missing = [f for f in required_fields if not str(data.get(f, "")).strip()]

    if missing:
        return jsonify({"error": f"Field berikut wajib diisi: {', '.join(missing)}"}), 400

    nim = data["nim"].strip()
    nama = data["nama"].strip()
    email = data["email"].strip()
    password = data["password"]

    if User.query.get(nim):
        return jsonify({"error": "NIM sudah terdaftar"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email sudah terdaftar"}), 400

    try:
        new_user = User(
            nim=nim,
            nama=nama,
            email=email,
            password=generate_password_hash(password),
            role="mahasiswa",
        )

        db.session.add(new_user)
        db.session.commit()

        return jsonify({"message": "Registrasi berhasil"}), 201

    except Exception:
        db.session.rollback()
        return jsonify({"error": "Terjadi kesalahan server, coba lagi"}), 500


# Login
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Request body tidak valid"}), 400

    if not data.get("nim") or not data.get("password"):
        return jsonify({"error": "NIM dan password wajib diisi"}), 400

    nim = data["nim"].strip()
    password = data["password"]

    user = User.query.get(nim)

    if not user or not check_password_hash(user.password, password):
        return jsonify({"error": "NIM atau password salah"}), 401

    session["user_nim"] = user.nim
    session["user_role"] = user.role
    session["user_nama"] = user.nama

    token = create_token(user.nim)

    return jsonify({
        "message": "Login sukses",
        "token": token,
        "user": {
            "nim": user.nim,
            "nama": user.nama,
            "email": user.email,
            "role": user.role,
        },
    }), 200


# ME
@auth_bp.route("/me", methods=["GET"])
@token_required
def get_me(user):
    return jsonify({
        "nim": user.nim,
        "nama": user.nama,
        "email": user.email,
        "role": user.role,
    }), 200


# Logout
@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"}), 200