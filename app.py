import os
from flask import Flask, jsonify
from flask_cors import CORS
from src.api.auth.routes import auth_bp, db
from src.api.chatbot.routes import chatbot_bp
from src.api.admin.routes import admin_bp
from flask_migrate import Migrate

app = Flask(__name__)
migrate = Migrate(app, db)

IS_PROD = os.getenv('FLASK_ENV') == 'production'

app.config['SQLALCHEMY_DATABASE_URI']        = os.getenv('DATABASE_URL', 'sqlite:///project.db')
app.config['SECRET_KEY']                     = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_HTTPONLY']        = True
app.config['SESSION_COOKIE_SAMESITE']        = 'Lax' if IS_PROD else 'None'
app.config['SESSION_COOKIE_SECURE']          = IS_PROD

FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')

CORS(
    app,
    supports_credentials=True,
    origins=[
        "http://localhost:5173",
        "http://192.168.1.5:5173",
        "http://192.168.1.15:5173",
        "https://chatbotfik-frontend.vercel.app",
        FRONTEND_URL,
    ],
    allow_headers=["Content-Type"],
    methods=["GET", "POST", "DELETE", "OPTIONS", "PUT"],
)

db.init_app(app)

app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(chatbot_bp, url_prefix='/api/chatbot')
app.register_blueprint(admin_bp, url_prefix='/api/admin')

with app.app_context():
    import src.models  # noqa: F401
    db.create_all()

@app.route("/")
def index():
    return jsonify({"status": "Server ChatbotFIK running ✓"}), 200

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=True,
        use_reloader=True,
        reloader_type='stat'
    )