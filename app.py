import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_session import Session
from src.api.auth.routes import auth_bp, db
from src.api.chatbot.routes import chatbot_bp
from src.api.admin.routes import admin_bp
from flask_migrate import Migrate

app = Flask(__name__)
migrate = Migrate(app, db)

# ─────────────────────────────────────────────────────────────
# KONFIGURASI
# ─────────────────────────────────────────────────────────────

app.config['SQLALCHEMY_DATABASE_URI']        = os.getenv('DATABASE_URL', 'sqlite:///project.db')
app.config['SECRET_KEY']                     = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Session disimpan di server (database), bukan di cookie browser
# Ini mengatasi masalah cross-origin cookie di production
app.config['SESSION_TYPE']                   = 'sqlalchemy'
app.config['SESSION_SQLALCHEMY_TABLE']       = 'flask_sessions'
app.config['SESSION_PERMANENT']              = False
app.config['SESSION_USE_SIGNER']             = True

# Cookie tetap perlu setting ini untuk cross-origin (Vercel <-> Railway)
app.config['SESSION_COOKIE_HTTPONLY']        = True
app.config['SESSION_COOKIE_SAMESITE']        = 'None'
app.config['SESSION_COOKIE_SECURE']          = True

# ─────────────────────────────────────────────────────────────
# CORS
# ─────────────────────────────────────────────────────────────

FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')

CORS(
    app,
    supports_credentials=True,
    origins=[
        "http://localhost:5173",
        "https://chatbotfik-frontend.vercel.app",
        FRONTEND_URL,
    ],
    allow_headers=["Content-Type"],
    methods=["GET", "POST", "DELETE", "OPTIONS", "PUT"],
)

# ─────────────────────────────────────────────────────────────
# DATABASE & SESSION
# ─────────────────────────────────────────────────────────────

db.init_app(app)

# Session harus diinisialisasi setelah db.init_app
app.config['SESSION_SQLALCHEMY'] = db
Session(app)

# ─────────────────────────────────────────────────────────────
# BLUEPRINTS
# ─────────────────────────────────────────────────────────────

app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(chatbot_bp, url_prefix='/api/chatbot')
app.register_blueprint(admin_bp, url_prefix='/api/admin')

# ─────────────────────────────────────────────────────────────
# BUAT TABEL
# ─────────────────────────────────────────────────────────────

with app.app_context():
    import src.models  # noqa: F401
    db.create_all()

# ─────────────────────────────────────────────────────────────
# ROUTES DASAR
# ─────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return jsonify({"status": "Server ChatbotFIK running ✓"}), 200

# ─────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=True,
        use_reloader=True,
        reloader_type='stat'
    )
