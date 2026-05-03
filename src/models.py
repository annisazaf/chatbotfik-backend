from datetime import datetime
from src.api.auth.routes import db

# MODEL KURIKULUM PRODI

class KurikulumProdi(db.Model):
    """
    Master data program studi beserta aturan akademiknya.
    Menggantikan hardcode di src/rules/academic_rules.py.
    """
    __tablename__ = 'kurikulum_prodi'

    id                = db.Column(db.Integer, primary_key=True)
    nama_prodi        = db.Column(db.String(100), nullable=False, unique=True)
    total_semester    = db.Column(db.Integer, nullable=False, default=8)
    sks_lulus         = db.Column(db.Integer, nullable=False, default=144)
    syarat_sidang_sks = db.Column(db.Integer, nullable=False, default=138)
    is_active         = db.Column(db.Boolean, nullable=False, default=True)

    # Aturan peminatan disimpan sebagai JSON agar fleksibel
    # Format: {"harus_konsisten": true, "min_mk_per_jalur": 3,
    #           "jalur": {"CE": "Cybersecurity", "NE": "Network", "SE": "Software Engineering"}}
    peminatan_config  = db.Column(db.JSON, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    mata_kuliah = db.relationship(
        'MataKuliahKurikulum',
        backref='prodi',
        lazy=True,
        order_by='MataKuliahKurikulum.semester, MataKuliahKurikulum.urutan',
        cascade='all, delete-orphan'
    )

    def to_dict(self, include_mk=False):
        data = {
            'id':                self.id,
            'nama_prodi':        self.nama_prodi,
            'total_semester':    self.total_semester,
            'sks_lulus':         self.sks_lulus,
            'syarat_sidang_sks': self.syarat_sidang_sks,
            'is_active':         self.is_active,
            'peminatan_config':  self.peminatan_config,
            'total_mk':          len(self.mata_kuliah),
            'total_sks':         sum(mk.sks for mk in self.mata_kuliah),
            'created_at':        self.created_at.isoformat(),
            'updated_at':        self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_mk:
            data['mata_kuliah'] = [mk.to_dict() for mk in self.mata_kuliah]
        return data


# MODEL MATA KULIAH KURIKULUM

class MataKuliahKurikulum(db.Model):
    """
    Daftar mata kuliah per program studi.
    Menggantikan pembacaan langsung dari file XLSX.
    """
    __tablename__ = 'mata_kuliah_kurikulum'

    id         = db.Column(db.Integer, primary_key=True)
    prodi_id   = db.Column(db.Integer, db.ForeignKey('kurikulum_prodi.id'), nullable=False, index=True)
    kode       = db.Column(db.String(20), nullable=True)
    nama       = db.Column(db.String(200), nullable=False)
    sks        = db.Column(db.Integer, nullable=False)
    semester   = db.Column(db.Integer, nullable=False)
    keterangan = db.Column(db.String(100), nullable=True)
    # Contoh: "MKWU", "MKPS", "MBKM", "Peminatan CE.1", "Pilihan"
    prasyarat  = db.Column(db.Text, nullable=True)
    urutan     = db.Column(db.Integer, nullable=False, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id':         self.id,
            'prodi_id':   self.prodi_id,
            'kode':       self.kode,
            'nama':       self.nama,
            'sks':        self.sks,
            'semester':   self.semester,
            'keterangan': self.keterangan,
            'prasyarat':  self.prasyarat,
            'urutan':     self.urutan,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


# MODEL KHS UPLOAD

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


# MODEL CHAT SESSION

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


# MODEL CHAT MESSAGE

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