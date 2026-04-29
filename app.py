import os
from dotenv import load_dotenv

load_dotenv()

from flask import Flask, jsonify
from flask_cors import CORS
from src.api.auth.routes import auth_bp, db
from src.api.chatbot.routes import chatbot_bp
from src.api.admin.routes import admin_bp
from flask_migrate import Migrate


app = Flask(__name__)

database_url = os.getenv("DATABASE_URL")

if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url or "sqlite:///project.db"
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_COOKIE_SAMESITE"] = "None"
app.config["SESSION_COOKIE_SECURE"] = True

frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")

CORS(
    app,
    supports_credentials=True,
    origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "https://chatbotfik-frontend.vercel.app",
        frontend_url,
    ],
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
)

db.init_app(app)
migrate = Migrate(app, db)

app.register_blueprint(auth_bp, url_prefix="/api")
app.register_blueprint(chatbot_bp, url_prefix="/api/chatbot")
app.register_blueprint(admin_bp, url_prefix="/api/admin")


with app.app_context():
    import src.models  # noqa: F401

    db.create_all()

    print("====================================")
    print("DATABASE_URL terbaca:", bool(database_url))
    print("Database dipakai:", app.config["SQLALCHEMY_DATABASE_URI"])
    print("====================================")


@app.route("/")
def index():
    return jsonify({"status": "Server ChatbotFIK running ✓"}), 200


@app.route("/debug-db")
def debug_db():
    return jsonify({
        "database_url_terbaca": bool(database_url),
        "database_dipakai": app.config["SQLALCHEMY_DATABASE_URI"],
    }), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=True,
        use_reloader=True,
        reloader_type="stat",
    )