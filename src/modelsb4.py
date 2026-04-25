"""
Models - ChatbotFIK
Lokasi: src/models.py


from datetime import datetime
from src.api.auth.routes import db


# ─────────────────────────────────────────────
# MODEL KHS UPLOAD
# ─────────────────────────────────────────────

class KHSUpload(db.Model):
    __tablename__ = 'khs_uploads'

    id           = db.Column(db.Integer, primary_key=True)
    nim          = db.Column(db.String(20), nullable=False, index=True)
    upload_time  = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    hasil_json        = db.Column(db.JSON, nullable=True)
    rekomendasi_json  = db.Column(db.JSON, nullable=True)   # cache hasil AI rekomendasi

    # Relasi ke chat sessions
    chat_sessions = db.relationship('ChatSession', backref='khs_upload', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id':          self.id,
            'nim':         self.nim,
            'upload_time': self.upload_time.isoformat(),
            'hasil':       self.hasil_json,
        }


# ─────────────────────────────────────────────
# MODEL CHAT SESSION
# ─────────────────────────────────────────────

class ChatSession(db.Model):
    __tablename__ = 'chat_sessions'

    id             = db.Column(db.String(36), primary_key=True)   # UUID
    nim            = db.Column(db.String(20), nullable=False, index=True)
    khs_upload_id  = db.Column(db.Integer, db.ForeignKey('khs_uploads.id'), nullable=True)
    system_prompt  = db.Column(db.Text, nullable=True)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_active    = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    title          = db.Column(db.String(200), nullable=True)      # judul sesi, diambil dari pesan pertama

    # Relasi ke pesan-pesan
    messages = db.relationship(
        'ChatMessage',
        backref='session',
        lazy=True,
        order_by='ChatMessage.created_at',
        cascade='all, delete-orphan'
    )

    def to_dict(self, include_messages=False):
        data = {
            'session_id':   self.id,
            'nim':          self.nim,
            'title':        self.title or 'Chat tanpa judul',
            'created_at':   self.created_at.isoformat(),
            'last_active':  self.last_active.isoformat() if self.last_active else None,
            'khs_upload_id': self.khs_upload_id,
            'message_count': len(self.messages),
        }
        if include_messages:
            data['messages'] = [m.to_dict() for m in self.messages]
        return data


# ─────────────────────────────────────────────
# MODEL CHAT MESSAGE
# ─────────────────────────────────────────────

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'

    id         = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), db.ForeignKey('chat_sessions.id'), nullable=False, index=True)
    role       = db.Column(db.String(20), nullable=False)   # 'user' atau 'assistant'
    content    = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id':         self.id,
            'role':       self.role,
            'content':    self.content,
            'created_at': self.created_at.isoformat(),
        }
"""