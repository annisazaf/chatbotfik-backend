import uuid
from datetime import datetime
from pathlib import Path

from flask import Blueprint, request, jsonify
from src.api.auth.routes import db, get_nim_from_token
from src.models import KHSUpload, ChatSession, ChatMessage
from src.chatbot import proses_khs, build_system_prompt, chat as ai_chat, get_pengetahuan_tambahan

chatbot_bp = Blueprint('chatbot', __name__)

UPLOAD_DIR = Path("uploads_temp")
UPLOAD_DIR.mkdir(exist_ok=True)

MAX_HISTORY_IN_MEMORY = 20   # pesan terakhir yang dikirim ke LLM sebagai konteks


# Helper
def get_logged_in_nim():
    """Return NIM dari JWT token, atau None"""
    return get_nim_from_token()


def require_login():
    """Return (nim, None) jika login, atau (None, response 401)."""
    nim = get_logged_in_nim()
    if not nim:
        return None, jsonify({"error": "Unauthorized. Silakan login terlebih dahulu."}), 401
    return nim, None


def build_history_for_llm(chat_session: ChatSession) -> list[dict]:
    """
    Ambil N pesan terakhir dari database dan format menjadi list
    [{"role": "user"|"assistant", "content": "..."}]
    yang siap dikirim ke LLM
    """
    messages = (
        ChatMessage.query
        .filter_by(session_id=chat_session.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(MAX_HISTORY_IN_MEMORY)
        .all()
    )
    # Balik urutan: dari lama ke baru
    messages = list(reversed(messages))
    return [{"role": m.role, "content": m.content} for m in messages]


def derive_session_title(pesan: str) -> str:
    """Mengambil 60 karakter pertama dari pesan pertama sebagai judul riwayat"""
    return pesan[:60] + ("..." if len(pesan) > 60 else "")


# Upload KHS untuk buat sesi chat baru
@chatbot_bp.route("/upload", methods=["POST"])
def upload_khs():
    nim, err = require_login()
    if err:
        return err

    if "file" not in request.files:
        return jsonify({"error": "Tidak ada file yang diupload."}), 400

    file = request.files["file"]
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "File harus berformat PDF."}), 400

    session_id = str(uuid.uuid4())
    pdf_path = UPLOAD_DIR / f"{session_id}.pdf"
    file.save(pdf_path)

    try:
        # 1. Ekstrak data dari PDF
        hasil = proses_khs(str(pdf_path))

        # 2. Simpan KHS ke database
        khs_upload = KHSUpload(
            nim=nim,
            upload_time=datetime.utcnow(),
            hasil_json=hasil,
        )
        db.session.add(khs_upload)
        db.session.flush()   # dapat id sebelum commit

        # 3. Bangun system prompt untuk LLM
        system_prompt = build_system_prompt(hasil)

        # 4. Buat chat session di database
        chat_session = ChatSession(
            id=session_id,
            nim=nim,
            khs_upload_id=khs_upload.id,
            system_prompt=system_prompt,
            created_at=datetime.utcnow(),
            last_active=datetime.utcnow(),
            title=f"KHS {hasil.get('nama_mahasiswa', nim)} - {datetime.utcnow().strftime('%d %b %Y')}",
        )
        db.session.add(chat_session)
        db.session.commit()

        # 5. Hitung statistik untuk response
        total_sks = hasil.get('total_sks_kurikulum', 0)
        persen = (hasil.get('sks_sudah_tempuh', 0) / total_sks * 100) if total_sks > 0 else 0

        return jsonify({
            "session_id":session_id,
            "khs_id":khs_upload.id,
            "nama":hasil.get("nama_mahasiswa"),
            "nim":hasil.get("nim"),
            "prodi":hasil.get("program_studi"),
            "ipk":hasil.get("ipk"),
            "ips":hasil.get("ips"),
            "sks_tempuh":hasil.get("sks_sudah_tempuh"),
            "sks_total":total_sks,
            "sks_sisa":hasil.get("sks_belum_tempuh"),
            "mk_lulus":hasil.get("jumlah_mk_lulus"),
            "mk_belum":hasil.get("jumlah_mk_belum"),
            "persen":round(persen, 1),
        }), 200

    except Exception as e:
        db.session.rollback()
        if pdf_path.exists():
            pdf_path.unlink()
        return jsonify({"error": f"Gagal memproses KHS: {str(e)}"}), 500

    finally:
        # Hapus file temp setelah diproses (sukses maupun gagal)
        if pdf_path.exists():
            pdf_path.unlink()


# Chat, kirim pesan, dapat respons
@chatbot_bp.route("/chat", methods=["POST"])
def chat_endpoint():
    
    nim, err = require_login()
    if err:
        return err

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body tidak valid atau bukan JSON."}), 400

    session_id = data.get("session_id", "").strip()
    pesan = data.get("pesan", "").strip()

    if not session_id:
        return jsonify({"error": "session_id harus disertakan."}), 400
    if not pesan:
        return jsonify({"error": "Pesan tidak boleh kosong."}), 400

    # Ambil sesi dari DB, pastikan milik user yang login
    chat_session = ChatSession.query.filter_by(id=session_id, nim=nim).first()
    if not chat_session:
        return jsonify({"error": "Sesi tidak ditemukan atau bukan milik Anda."}), 404

    # Set judul sesi dari pesan pertama jika belum ada
    is_first_message = ChatMessage.query.filter_by(session_id=session_id).count() == 0
    if is_first_message and not chat_session.title:
        chat_session.title = derive_session_title(pesan)

    try:
        # Ambil history dari DB untuk konteks LLM
        history = build_history_for_llm(chat_session)

        # Gabungkan system prompt mahasiswa + pengetahuan tambahan dari admin
        system_prompt = chat_session.system_prompt + get_pengetahuan_tambahan()

        # Panggil AI
        jawaban = ai_chat(pesan, history, system_prompt)

        # Simpan pesan user ke DB
        db.session.add(ChatMessage(
            session_id=session_id,
            role='user',
            content=pesan,
            created_at=datetime.utcnow(),
        ))

        # Simpan balasan AI ke DB
        db.session.add(ChatMessage(
            session_id=session_id,
            role='assistant',
            content=jawaban,
            created_at=datetime.utcnow(),
        ))

        # Update last_active sesi
        chat_session.last_active = datetime.utcnow()
        db.session.commit()

        return jsonify({"jawaban": jawaban, "session_id": session_id}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Gagal mendapatkan respons AI: {str(e)}"}), 500


# List semua sesi chat user (riwayat chat) diurutkan dari yang terbaru digunakan
@chatbot_bp.route("/sessions", methods=["GET"])
def list_sessions():
    
    nim, err = require_login()
    if err:
        return err

    sessions_list = (
        ChatSession.query
        .filter_by(nim=nim)
        .order_by(ChatSession.last_active.desc())
        .all()
    )

    return jsonify({
        "sessions": [s.to_dict() for s in sessions_list],
        "total": len(sessions_list),
    }), 200


# Detail sesi chat dan full history pesan
@chatbot_bp.route("/sessions/<session_id>", methods=["GET"])
def get_session(session_id):
    """Dipakai frontend saat user membuka/melanjutkan sesi lama"""
    nim, err = require_login()
    if err:
        return err

    chat_session = ChatSession.query.filter_by(id=session_id, nim=nim).first()
    if not chat_session:
        return jsonify({"error": "Sesi tidak ditemukan atau bukan milik Anda."}), 404

    return jsonify(chat_session.to_dict(include_messages=True)), 200


# Data KHS dari sesi tertentu yang dipilih (tidak perlu re-upload)
@chatbot_bp.route("/sessions/<session_id>/khs", methods=["GET"])
def get_session_khs(session_id):
    
    nim, err = require_login()
    if err:
        return err

    chat_session = ChatSession.query.filter_by(id=session_id, nim=nim).first()
    if not chat_session:
        return jsonify({"error": "Sesi tidak ditemukan atau bukan milik Anda."}), 404

    if not chat_session.khs_upload:
        return jsonify({"error": "Tidak ada data KHS yang terhubung ke sesi ini."}), 404

    hasil = chat_session.khs_upload.hasil_json or {}
    total_sks = hasil.get('total_sks_kurikulum', 0)
    persen = (hasil.get('sks_sudah_tempuh', 0) / total_sks * 100) if total_sks > 0 else 0

    return jsonify({
        "khs_id":chat_session.khs_upload.id,
        "upload_time":chat_session.khs_upload.upload_time.isoformat(),
        "nama":hasil.get("nama_mahasiswa"),
        "nim":hasil.get("nim"),
        "prodi":hasil.get("program_studi"),
        "ipk":hasil.get("ipk"),
        "ips":hasil.get("ips"),
        "sks_tempuh":hasil.get("sks_sudah_tempuh"),
        "sks_total":total_sks,
        "sks_sisa":hasil.get("sks_belum_tempuh"),
        "mk_lulus":hasil.get("jumlah_mk_lulus"),
        "mk_belum":hasil.get("jumlah_mk_belum"),
        "persen":round(persen, 1),
    }), 200


# Hapus sesi chat
@chatbot_bp.route("/sessions/<session_id>", methods=["DELETE"])
def delete_session(session_id):
    
    nim, err = require_login()
    if err:
        return err

    chat_session = ChatSession.query.filter_by(id=session_id, nim=nim).first()
    if not chat_session:
        return jsonify({"error": "Sesi tidak ditemukan atau bukan milik Anda."}), 404

    try:
        db.session.delete(chat_session)
        db.session.commit()
        return jsonify({"message": "Sesi berhasil dihapus."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Gagal menghapus sesi: {str(e)}"}), 500


# Rekomendasi matkul dan karier
@chatbot_bp.route("/sessions/<session_id>/rekomendasi", methods=["GET"])
def get_rekomendasi(session_id):
    nim, err = require_login()
    if err:
        return err

    chat_session = ChatSession.query.filter_by(id=session_id, nim=nim).first()
    if not chat_session:
        return jsonify({"error": "Sesi tidak ditemukan atau bukan milik Anda."}), 404

    # Selalu ambil KHS terbaru milik user, bukan dari session
    khs = KHSUpload.query.filter_by(nim=nim)\
        .order_by(KHSUpload.upload_time.desc())\
        .first()

    if not khs:
        return jsonify({"error": "Tidak ada data KHS ditemukan."}), 404

    # Kalau sudah pernah di-generate, return cache
    if khs.rekomendasi_json:
        return jsonify(khs.rekomendasi_json), 200

    # Generate dari AI
    hasil = khs.hasil_json or {}

    mk_lulus_nama = {m["nama"].lower().strip() for m in hasil.get("mk_sudah_lulus", [])}
    mk_belum_list = hasil.get("mk_belum_diambil", [])

    prompt = f"""
Kamu adalah asisten akademik. Berdasarkan data KHS mahasiswa berikut, berikan rekomendasi dalam format JSON.

PENTING:
- Daftar mata kuliah yang SUDAH LULUS (JANGAN masukkan ke rekomendasi): {[m["nama"] for m in hasil.get("mk_sudah_lulus", [])]}
- Daftar mata kuliah yang BELUM DIAMBIL (sumber rekomendasi): {[m["nama"] for m in mk_belum_list]}

Data KHS lengkap:
{hasil}

Berikan response dalam format JSON berikut (HANYA JSON, tanpa teks lain).
PASTIKAN mk_eligible HANYA berisi mata kuliah dari daftar BELUM DIAMBIL di atas:
{{
    "mk_eligible": [
        {{"nama": "Nama MK", "sks": 3, "alasan": "Prasyarat Terpenuhi"}}
    ],
    "mk_belum": [
        {{"nama": "Nama MK", "alasan": "Belum Memenuhi Prasyarat", "keterangan": "Detail prasyarat yang kurang"}}
    ],
    "strategi": "Teks rekomendasi strategi akademik...",
    "karier": "Teks rekomendasi karier..."
}}
    """

    try:
        import json
        import re
        from src.chatbot import chat as ai_chat

        raw = ai_chat(prompt, [], "Kamu adalah asisten akademik yang menghasilkan output JSON.", max_tokens=4096)
        cleaned = re.sub(r"```json|```", "", raw).strip()
        rekomendasi = json.loads(cleaned)

        # Filter keamanan: buang MK yang sudah lulus dari mk_eligible
        def sudah_lulus(nama_mk: str) -> bool:
            n = nama_mk.lower().strip()
            return n in mk_lulus_nama or any(n in lulus or lulus in n for lulus in mk_lulus_nama)

        rekomendasi["mk_eligible"] = [
            mk for mk in rekomendasi.get("mk_eligible", [])
            if not sudah_lulus(mk.get("nama", ""))
        ]

        # Cache ke DB
        khs.rekomendasi_json = rekomendasi
        db.session.commit()

        return jsonify(rekomendasi), 200

    except Exception as e:
        import traceback
        traceback.print_exc()  # ini print full error ke terminal
        return jsonify({"error": f"Gagal generate rekomendasi: {str(e)}"}), 500


@chatbot_bp.route("/khs/latest", methods=["GET"])
def get_latest_khs():
    nim, err = require_login()
    if err:
        return err

    latest = KHSUpload.query.filter_by(nim=nim)\
        .order_by(KHSUpload.upload_time.desc())\
        .first()

    if not latest or not latest.hasil_json:
        return jsonify({"has_khs": False}), 200

    hasil = latest.hasil_json
    return jsonify({
        "has_khs":    True,
        "nama":hasil.get("nama_mahasiswa"),
        "nim":hasil.get("nim"),
        "ipk":hasil.get("ipk"),
        "ips":hasil.get("ips"),
        "sks_tempuh":hasil.get("sks_sudah_tempuh"),
        "sks_total":144,
        "persen":round(hasil.get("sks_sudah_tempuh", 0) / 144 * 100, 1),
        "mk_lulus":hasil.get("jumlah_mk_lulus"),
        "upload_time":latest.upload_time.isoformat(),
    }), 200

"""
Endpoints:
  POST   /api/chatbot/upload = Upload PDF KHS, init sesi chat
  POST   /api/chatbot/chat = Kirim pesan, dapat balasan AI
  GET    /api/chatbot/sessions = List semua sesi chat milik user
  GET    /api/chatbot/sessions/<id> = Detail sesi + full history pesan
  DELETE /api/chatbot/sessions/<id> = Hapus sesi chat
  GET    /api/chatbot/sessions/<id>/khs = Data KHS dari sesi tertentu
"""