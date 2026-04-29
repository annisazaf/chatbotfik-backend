"""
Admin Routes - ChatbotFIK
Lokasi: src/api/admin/routes.py

Hanya bisa diakses oleh user dengan role='admin'.

Endpoints:
  GET    /api/admin/prodi                    → list semua prodi
  POST   /api/admin/prodi                    → tambah prodi baru
  PUT    /api/admin/prodi/<id>               → edit prodi
  DELETE /api/admin/prodi/<id>               → hapus prodi
  GET    /api/admin/prodi/<id>/mk            → list MK satu prodi
  POST   /api/admin/mk                       → tambah MK
  PUT    /api/admin/mk/<id>                  → edit MK
  DELETE /api/admin/mk/<id>                  → hapus MK
  POST   /api/admin/import-xlsx              → import kurikulum dari upload XLSX
"""

from flask import Blueprint, request, jsonify
from src.api.auth.routes import db, User
from src.models import KurikulumProdi, MataKuliahKurikulum
from src.chatbot import reload_kurikulum

admin_bp = Blueprint('admin', __name__)


# ─────────────────────────────────────────────
# HELPER: cek login admin
# ─────────────────────────────────────────────

def get_nim_from_token():
    """Ambil NIM dari JWT Authorization header."""
    import jwt, os
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    token = auth_header.split(' ', 1)[1]
    try:
        payload = jwt.decode(token, os.getenv('SECRET_KEY', 'dev-secret-key'), algorithms=['HS256'])
        return payload.get('nim')
    except Exception:
        return None


def require_admin():
    """Return (user, None) jika admin, atau (None, response error)."""
    nim = get_nim_from_token()
    if not nim:
        return None, (jsonify({"error": "Unauthorized. Silakan login."}), 401)

    user = User.query.get(nim)
    if not user or user.role != 'admin':
        return None, (jsonify({"error": "Forbidden. Hanya admin yang dapat mengakses fitur ini."}), 403)

    return user, None


# ─────────────────────────────────────────────
# CEK STATUS ADMIN
# ─────────────────────────────────────────────

@admin_bp.route("/check", methods=["GET"])
def check_admin():
    """Endpoint untuk frontend cek apakah user yang login adalah admin."""
    user, err = require_admin()
    if err:
        return err
    return jsonify({"is_admin": True, "nim": user.nim, "nama": user.nama}), 200


# ─────────────────────────────────────────────
# CRUD PRODI
# ─────────────────────────────────────────────

@admin_bp.route("/prodi", methods=["GET"])
def list_prodi():
    """List semua program studi (aktif maupun tidak)."""
    _, err = require_admin()
    if err:
        return err

    semua = KurikulumProdi.query.order_by(KurikulumProdi.nama_prodi).all()
    return jsonify({
        "prodi": [p.to_dict() for p in semua],
        "total": len(semua),
    }), 200


@admin_bp.route("/prodi/<int:prodi_id>", methods=["GET"])
def get_prodi(prodi_id):
    """Detail satu prodi beserta semua mata kuliahnya."""
    _, err = require_admin()
    if err:
        return err

    prodi = KurikulumProdi.query.get(prodi_id)
    if not prodi:
        return jsonify({"error": "Program studi tidak ditemukan."}), 404

    return jsonify(prodi.to_dict(include_mk=True)), 200


@admin_bp.route("/prodi", methods=["POST"])
def tambah_prodi():
    """
    Tambah program studi baru.
    Body JSON:
      nama_prodi, total_semester, sks_lulus, syarat_sidang_sks,
      is_active (opsional, default True),
      peminatan_config (opsional)
    """
    _, err = require_admin()
    if err:
        return err

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body tidak valid."}), 400

    nama_prodi = (data.get("nama_prodi") or "").strip()
    if not nama_prodi:
        return jsonify({"error": "nama_prodi wajib diisi."}), 400

    if KurikulumProdi.query.filter_by(nama_prodi=nama_prodi).first():
        return jsonify({"error": f"Program studi '{nama_prodi}' sudah ada."}), 400

    # Validasi field angka
    for field in ["total_semester", "sks_lulus", "syarat_sidang_sks"]:
        val = data.get(field)
        if val is None or not str(val).isdigit():
            return jsonify({"error": f"Field '{field}' wajib diisi dengan angka."}), 400

    prodi = KurikulumProdi(
        nama_prodi        = nama_prodi,
        total_semester    = int(data["total_semester"]),
        sks_lulus         = int(data["sks_lulus"]),
        syarat_sidang_sks = int(data["syarat_sidang_sks"]),
        is_active         = bool(data.get("is_active", True)),
        peminatan_config  = data.get("peminatan_config"),
    )

    try:
        db.session.add(prodi)
        db.session.commit()
        reload_kurikulum()   # refresh cache
        return jsonify({"message": "Program studi berhasil ditambahkan.", "prodi": prodi.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Gagal menyimpan: {str(e)}"}), 500


@admin_bp.route("/prodi/<int:prodi_id>", methods=["PUT"])
def edit_prodi(prodi_id):
    """
    Edit program studi. Semua field opsional (partial update).
    Body JSON: nama_prodi, total_semester, sks_lulus, syarat_sidang_sks,
               is_active, peminatan_config
    """
    _, err = require_admin()
    if err:
        return err

    prodi = KurikulumProdi.query.get(prodi_id)
    if not prodi:
        return jsonify({"error": "Program studi tidak ditemukan."}), 404

    data = request.get_json(silent=True) or {}

    if "nama_prodi" in data:
        nama_baru = data["nama_prodi"].strip()
        existing = KurikulumProdi.query.filter_by(nama_prodi=nama_baru).first()
        if existing and existing.id != prodi_id:
            return jsonify({"error": f"Nama '{nama_baru}' sudah digunakan prodi lain."}), 400
        prodi.nama_prodi = nama_baru

    if "total_semester"    in data: prodi.total_semester    = int(data["total_semester"])
    if "sks_lulus"         in data: prodi.sks_lulus         = int(data["sks_lulus"])
    if "syarat_sidang_sks" in data: prodi.syarat_sidang_sks = int(data["syarat_sidang_sks"])
    if "is_active"         in data: prodi.is_active         = bool(data["is_active"])
    if "peminatan_config"  in data: prodi.peminatan_config  = data["peminatan_config"]

    try:
        db.session.commit()
        reload_kurikulum()
        return jsonify({"message": "Program studi berhasil diperbarui.", "prodi": prodi.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Gagal menyimpan: {str(e)}"}), 500


@admin_bp.route("/prodi/<int:prodi_id>", methods=["DELETE"])
def hapus_prodi(prodi_id):
    """
    Hapus program studi beserta semua mata kuliahnya (cascade).
    HATI-HATI: tidak bisa di-undo!
    """
    _, err = require_admin()
    if err:
        return err

    prodi = KurikulumProdi.query.get(prodi_id)
    if not prodi:
        return jsonify({"error": "Program studi tidak ditemukan."}), 404

    nama = prodi.nama_prodi
    try:
        db.session.delete(prodi)
        db.session.commit()
        reload_kurikulum()
        return jsonify({"message": f"Program studi '{nama}' dan seluruh mata kuliahnya berhasil dihapus."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Gagal menghapus: {str(e)}"}), 500


# ─────────────────────────────────────────────
# LIST MK PER PRODI
# ─────────────────────────────────────────────

@admin_bp.route("/prodi/<int:prodi_id>/mk", methods=["GET"])
def list_mk(prodi_id):
    """
    List semua mata kuliah satu prodi.
    Query param: ?semester=3 (opsional, filter per semester)
    """
    _, err = require_admin()
    if err:
        return err

    prodi = KurikulumProdi.query.get(prodi_id)
    if not prodi:
        return jsonify({"error": "Program studi tidak ditemukan."}), 404

    semester_filter = request.args.get("semester", type=int)

    query = MataKuliahKurikulum.query.filter_by(prodi_id=prodi_id)
    if semester_filter:
        query = query.filter_by(semester=semester_filter)

    mk_list = query.order_by(
        MataKuliahKurikulum.semester,
        MataKuliahKurikulum.urutan
    ).all()

    # Kelompokkan per semester untuk kemudahan tampilan
    per_semester = {}
    for mk in mk_list:
        sem = mk.semester
        if sem not in per_semester:
            per_semester[sem] = []
        per_semester[sem].append(mk.to_dict())

    return jsonify({
        "prodi_id":    prodi_id,
        "nama_prodi":  prodi.nama_prodi,
        "total_mk":    len(mk_list),
        "total_sks":   sum(mk.sks for mk in mk_list),
        "per_semester": per_semester,
        "mk":          [mk.to_dict() for mk in mk_list],
    }), 200


# ─────────────────────────────────────────────
# CRUD MATA KULIAH
# ─────────────────────────────────────────────

@admin_bp.route("/mk", methods=["POST"])
def tambah_mk():
    """
    Tambah mata kuliah baru ke satu prodi.
    Body JSON:
      prodi_id (wajib), nama (wajib), sks (wajib), semester (wajib),
      kode (opsional), keterangan (opsional), prasyarat (opsional)
    """
    _, err = require_admin()
    if err:
        return err

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body tidak valid."}), 400

    # Validasi field wajib
    for field in ["prodi_id", "nama", "sks", "semester"]:
        if not data.get(field):
            return jsonify({"error": f"Field '{field}' wajib diisi."}), 400

    prodi = KurikulumProdi.query.get(data["prodi_id"])
    if not prodi:
        return jsonify({"error": "Program studi tidak ditemukan."}), 404

    # Tentukan urutan: taruh di akhir semester tersebut
    urutan_terakhir = db.session.query(
        db.func.max(MataKuliahKurikulum.urutan)
    ).filter_by(
        prodi_id=data["prodi_id"],
        semester=int(data["semester"])
    ).scalar() or 0

    mk = MataKuliahKurikulum(
        prodi_id   = int(data["prodi_id"]),
        kode       = (data.get("kode") or "").strip(),
        nama       = data["nama"].strip(),
        sks        = int(data["sks"]),
        semester   = int(data["semester"]),
        keterangan = (data.get("keterangan") or "").strip() or None,
        prasyarat  = (data.get("prasyarat") or "").strip() or None,
        urutan     = urutan_terakhir + 1,
    )

    try:
        db.session.add(mk)
        db.session.commit()
        reload_kurikulum()
        return jsonify({"message": "Mata kuliah berhasil ditambahkan.", "mk": mk.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Gagal menyimpan: {str(e)}"}), 500


@admin_bp.route("/mk/<int:mk_id>", methods=["PUT"])
def edit_mk(mk_id):
    """
    Edit mata kuliah. Semua field opsional (partial update).
    Body JSON: kode, nama, sks, semester, keterangan, prasyarat
    """
    _, err = require_admin()
    if err:
        return err

    mk = MataKuliahKurikulum.query.get(mk_id)
    if not mk:
        return jsonify({"error": "Mata kuliah tidak ditemukan."}), 404

    data = request.get_json(silent=True) or {}

    if "kode"       in data: mk.kode       = (data["kode"] or "").strip()
    if "nama"       in data: mk.nama       = data["nama"].strip()
    if "sks"        in data: mk.sks        = int(data["sks"])
    if "semester"   in data: mk.semester   = int(data["semester"])
    if "keterangan" in data: mk.keterangan = (data["keterangan"] or "").strip() or None
    if "prasyarat"  in data: mk.prasyarat  = (data["prasyarat"] or "").strip() or None
    if "urutan"     in data: mk.urutan     = int(data["urutan"])

    try:
        db.session.commit()
        reload_kurikulum()
        return jsonify({"message": "Mata kuliah berhasil diperbarui.", "mk": mk.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Gagal menyimpan: {str(e)}"}), 500


@admin_bp.route("/mk/<int:mk_id>", methods=["DELETE"])
def hapus_mk(mk_id):
    """Hapus satu mata kuliah."""
    _, err = require_admin()
    if err:
        return err

    mk = MataKuliahKurikulum.query.get(mk_id)
    if not mk:
        return jsonify({"error": "Mata kuliah tidak ditemukan."}), 404

    nama = mk.nama
    try:
        db.session.delete(mk)
        db.session.commit()
        reload_kurikulum()
        return jsonify({"message": f"Mata kuliah '{nama}' berhasil dihapus."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Gagal menghapus: {str(e)}"}), 500


# ─────────────────────────────────────────────
# IMPORT XLSX
# ─────────────────────────────────────────────

@admin_bp.route("/import-xlsx", methods=["POST"])
def import_xlsx():
    """
    Upload file XLSX kurikulum → parse → simpan ke DB.
    Form-data: file (PDF), prodi_id (opsional: kalau ada, replace MK prodi tsb)

    Kalau prodi_id tidak dikirim, nama prodi dideteksi dari nama file.
    Kalau prodi sudah ada di DB, MK-nya akan di-replace (hapus lama, isi baru).
    Kalau prodi belum ada, akan dibuat baru dengan nilai default.
    """
    _, err = require_admin()
    if err:
        return err

    if "file" not in request.files:
        return jsonify({"error": "Tidak ada file yang diupload."}), 400

    file = request.files["file"]
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        return jsonify({"error": "File harus berformat .xlsx"}), 400

    import tempfile, os
    from src.curriculum.curriculum_loader import load_kurikulum
    from src.rules.academic_rules import ATURAN_PRODI, PEMINATAN_PRODI

    # Simpan file sementara
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    try:
        # Parse XLSX menggunakan loader lama
        kurikulum = load_kurikulum(tmp_path)

        # Cari atau buat prodi di DB
        prodi_id = request.form.get("prodi_id", type=int)
        if prodi_id:
            prodi = KurikulumProdi.query.get(prodi_id)
            if not prodi:
                return jsonify({"error": "prodi_id tidak ditemukan."}), 404
        else:
            prodi = KurikulumProdi.query.filter_by(
                nama_prodi=kurikulum.program_studi
            ).first()

            if not prodi:
                # Buat prodi baru dengan aturan dari academic_rules jika ada
                aturan    = ATURAN_PRODI.get(kurikulum.program_studi, {})
                peminatan = PEMINATAN_PRODI.get(kurikulum.program_studi, {})
                jalur = peminatan.get("jalur", {})
                prodi = KurikulumProdi(
                    nama_prodi        = kurikulum.program_studi,
                    total_semester    = aturan.get("total_semester", 8),
                    sks_lulus         = aturan.get("sks_lulus", 144),
                    syarat_sidang_sks = aturan.get("syarat_sidang_sks", 138),
                    is_active         = True,
                    peminatan_config  = {
                        "harus_konsisten":  peminatan.get("harus_konsisten", False),
                        "min_mk_per_jalur": peminatan.get("min_mk_per_jalur", 0),
                        "jalur":            jalur if isinstance(jalur, dict) else {},
                    } if peminatan else None,
                )
                db.session.add(prodi)
                db.session.flush()

        # Hapus semua MK lama prodi ini, ganti dengan yang baru
        MataKuliahKurikulum.query.filter_by(prodi_id=prodi.id).delete()

        for urutan, mk in enumerate(kurikulum.matakuliah):
            db.session.add(MataKuliahKurikulum(
                prodi_id   = prodi.id,
                kode       = mk.kode or "",
                nama       = mk.nama,
                sks        = mk.sks,
                semester   = mk.semester,
                keterangan = mk.keterangan,
                prasyarat  = mk.prasyarat,
                urutan     = urutan,
            ))

        db.session.commit()
        reload_kurikulum()

        return jsonify({
            "message":    f"Kurikulum '{kurikulum.program_studi}' berhasil diimport.",
            "prodi_id":   prodi.id,
            "nama_prodi": prodi.nama_prodi,
            "total_mk":   len(kurikulum.matakuliah),
            "total_sks":  kurikulum.total_sks,
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Gagal import: {str(e)}"}), 500

    finally:
        os.unlink(tmp_path)


# ─────────────────────────────────────────────
# DAFTAR USER TERDAFTAR
# ─────────────────────────────────────────────

@admin_bp.route("/users", methods=["GET"])
def list_users():
    """
    Tampilkan semua user yang sudah register.
    Query param: ?role=mahasiswa (opsional, filter by role)
    """
    _, err = require_admin()
    if err:
        return err

    role_filter = request.args.get("role")
    query = User.query
    if role_filter:
        query = query.filter_by(role=role_filter)

    users = query.order_by(User.nim).all()

    return jsonify({
        "total": len(users),
        "users": [
            {
                "nim":   u.nim,
                "nama":  u.nama,
                "email": u.email,
                "role":  u.role,
            }
            for u in users
        ],
    }), 200


@admin_bp.route("/users/<nim>/role", methods=["PUT"])
def ubah_role_user(nim):
    """
    Ubah role user (mahasiswa <-> admin).
    Hanya bisa dilakukan oleh admin yang sedang login.
    Admin tidak bisa mengubah role dirinya sendiri.
    Body JSON: { "role": "admin" } atau { "role": "mahasiswa" }
    """
    current_user, err = require_admin()
    if err:
        return err

    # Tidak boleh ubah role diri sendiri
    if current_user.nim == nim:
        return jsonify({"error": "Tidak dapat mengubah role akun Anda sendiri."}), 400

    target = User.query.get(nim)
    if not target:
        return jsonify({"error": "Pengguna tidak ditemukan."}), 404

    data = request.get_json(silent=True) or {}
    new_role = data.get("role", "").strip().lower()

    if new_role not in ("admin", "mahasiswa"):
        return jsonify({"error": "Role harus 'admin' atau 'mahasiswa'."}), 400

    target.role = new_role
    try:
        db.session.commit()
        return jsonify({
            "message": f"Role {target.nama} berhasil diubah menjadi '{new_role}'.",
            "nim":  target.nim,
            "nama": target.nama,
            "role": target.role,
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Gagal menyimpan: {str(e)}"}), 500
