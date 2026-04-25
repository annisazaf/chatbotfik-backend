"""
Flask Web App - ChatbotFIK
Lokasi: app.py (root folder)


import os
from flask import Flask, jsonify
from flask_cors import CORS

from src.api.auth.routes import auth_bp, db
from src.api.chatbot.routes import chatbot_bp
from flask_migrate import Migrate

# ─────────────────────────────────────────────
# INISIALISASI APP
# ─────────────────────────────────────────────

app = Flask(__name__)
migrate = Migrate(app, db)

# ─────────────────────────────────────────────
# KONFIGURASI
# ─────────────────────────────────────────────

app.config['SQLALCHEMY_DATABASE_URI']        = os.getenv('DATABASE_URL', 'sqlite:///project.db')
app.config['SECRET_KEY']                     = os.getenv('SECRET_KEY', 'dev-secret-key-ganti-di-production')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_HTTPONLY']        = True
# SESSION_COOKIE_SAMESITE → biarkan default Flask (Lax), aman untuk same-origin
# SESSION_COOKIE_SECURE   → aktifkan hanya di production (HTTPS)

# ─────────────────────────────────────────────
# CORS
# ─────────────────────────────────────────────

CORS(
    app,
    supports_credentials=True,
    origins=["http://localhost:5173"],
    allow_headers=["Content-Type"],
    methods=["GET", "POST", "DELETE", "OPTIONS"],
)

# ─────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────

db.init_app(app)

# ─────────────────────────────────────────────
# BLUEPRINTS
# ─────────────────────────────────────────────

# Auth  → /api/login, /api/register, /api/logout, /api/me
app.register_blueprint(auth_bp, url_prefix='/api')

# Chatbot → /api/chatbot/upload, /api/chatbot/chat,
#            /api/chatbot/sessions, /api/chatbot/sessions/<id>, dll.
app.register_blueprint(chatbot_bp, url_prefix='/api/chatbot')

# ─────────────────────────────────────────────
# BUAT TABEL
# ─────────────────────────────────────────────

with app.app_context():
    # Import models agar SQLAlchemy mengenali semua tabel sebelum create_all()
    import src.models  # noqa: F401
    db.create_all()

# ─────────────────────────────────────────────
# ROUTES DASAR
# ─────────────────────────────────────────────

@app.route("/")
def index():
    return jsonify({"status": "Server ChatbotFIK running ✓"}), 200


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, port=5000)
    
"""