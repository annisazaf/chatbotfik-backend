import io
import re
import openpyxl
from flask import Blueprint, request, jsonify, session
from src.api.auth.routes import db, User, get_nim_from_token
from src.models import KurikulumProdi, MataKuliahKurikulum, InformasiChatbot
from src.chatbot import reload_kurikulum

admin_bp = Blueprint('admin', __name__)


# Cek login admin
def require_admin():
    """Cek admin dari session atau JWT"""
    nim = session.get("user_nim") or get_nim_from_token()

    if not nim:
        return None, (jsonify({"error": "Unauthorized. Silakan login."}), 401)

    user = User.query.get(nim)

    if not user or user.role != 'admin':
        return None, (jsonify({"error": "Hanya admin yang dapat mengakses fitur ini."}), 403)

    return user, None


# Cek status admin
@admin_bp.route("/check", methods=["GET"])
def check_admin():
    user, err = require_admin()
    if err:
        return err
    return jsonify({"is_admin": True, "nim": user.nim, "nama": user.nama}), 200


# Create Read Delete Update Prodi
@admin_bp.route("/prodi", methods=["GET"])
def list_prodi():
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
    _, err = require_admin()
    if err:
        return err

    prodi = KurikulumProdi.query.get(prodi_id)

    if not prodi:
        return jsonify({"error": "Program studi tidak ditemukan."}), 404

    return jsonify(prodi.to_dict(include_mk=True)), 200


@admin_bp.route("/prodi", methods=["POST"])
def tambah_prodi():
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

    prodi = KurikulumProdi(
        nama_prodi=nama_prodi,
        total_semester=int(data["total_semester"]),
        sks_lulus=int(data["sks_lulus"]),
        syarat_sidang_sks=int(data["syarat_sidang_sks"]),
        is_active=bool(data.get("is_active", True)),
    )

    db.session.add(prodi)
    db.session.commit()
    reload_kurikulum()

    return jsonify({"message": "Prodi berhasil ditambahkan", "prodi": prodi.to_dict()}), 201


@admin_bp.route("/prodi/<int:prodi_id>", methods=["DELETE"])
def hapus_prodi(prodi_id):
    _, err = require_admin()
    if err:
        return err

    prodi = KurikulumProdi.query.get(prodi_id)

    if not prodi:
        return jsonify({"error": "Prodi tidak ditemukan"}), 404

    db.session.delete(prodi)
    db.session.commit()
    reload_kurikulum()

    return jsonify({"message": "Prodi berhasil dihapus"}), 200

# List user (page admin)
@admin_bp.route("/users", methods=["GET"])
def list_users():
    _, err = require_admin()
    if err:
        return err

    users = User.query.order_by(User.nim).all()

    return jsonify({
        "total": len(users),
        "users": [
            {
                "nim": u.nim,
                "nama": u.nama,
                "email": u.email,
                "role": u.role,
            }
            for u in users
        ],
    }), 200

# Ubah role user (mahasiswa - admin)
@admin_bp.route("/users/<string:nim>/role", methods=["PUT"])
def update_user_role(nim):
    _, err = require_admin()
    if err:
        return err

    data = request.get_json()

    user = User.query.get(nim)
    if not user:
        return jsonify({"error": "User tidak ditemukan"}), 404

    new_role = data.get("role")

    if new_role not in ["admin", "mahasiswa"]:
        return jsonify({"error": "Role tidak valid"}), 400

    user.role = new_role
    db.session.commit()

    return jsonify({"message": "Role berhasil diubah"}), 200

# List matkul
@admin_bp.route("/prodi/<int:prodi_id>/mk", methods=["GET"])
def list_mk(prodi_id):
    _, err = require_admin()
    if err:
        return err

    mk_list = MataKuliahKurikulum.query.filter_by(prodi_id=prodi_id).all()

    return jsonify({
        "mk": [mk.to_dict() for mk in mk_list],
        "total": len(mk_list),
    }), 200


# Create Read Delete Update Matkul
@admin_bp.route("/mk", methods=["POST"])
def tambah_mk():
    _, err = require_admin()
    if err:
        return err

    data = request.get_json()

    mk = MataKuliahKurikulum(
        prodi_id=data["prodi_id"],
        kode=(data.get("kode") or "").strip(),
        nama=data["nama"],
        sks=int(data["sks"]),
        semester=int(data["semester"]),
        keterangan=(data.get("keterangan") or "").strip() or None,
        prasyarat=(data.get("prasyarat") or "").strip() or None,
    )

    db.session.add(mk)
    db.session.commit()
    reload_kurikulum()

    return jsonify({"message": "MK berhasil ditambahkan"}), 201


@admin_bp.route("/mk/<int:mk_id>", methods=["DELETE"])
def hapus_mk(mk_id):
    _, err = require_admin()
    if err:
        return err

    mk = MataKuliahKurikulum.query.get(mk_id)

    if not mk:
        return jsonify({"error": "MK tidak ditemukan"}), 404

    db.session.delete(mk)
    db.session.commit()
    reload_kurikulum()

    return jsonify({"message": "MK berhasil dihapus"}), 200


@admin_bp.route("/mk/<int:mk_id>", methods=["PUT"])
def edit_mk(mk_id):
    _, err = require_admin()
    if err:
        return err

    mk = MataKuliahKurikulum.query.get(mk_id)
    if not mk:
        return jsonify({"error": "MK tidak ditemukan"}), 404

    data = request.get_json(silent=True) or {}

    if "kode" in data:
        mk.kode = (data["kode"] or "").strip()
    if "nama" in data:
        mk.nama = data["nama"]
    if "sks" in data:
        mk.sks = int(data["sks"])
    if "semester" in data:
        mk.semester = int(data["semester"])
    if "keterangan" in data:
        mk.keterangan = (data["keterangan"] or "").strip() or None
    if "prasyarat" in data:
        mk.prasyarat = (data["prasyarat"] or "").strip() or None

    db.session.commit()
    reload_kurikulum()

    return jsonify({"message": "MK berhasil diperbarui", "mk": mk.to_dict()}), 200


@admin_bp.route("/prodi/<int:prodi_id>", methods=["PUT"])
def edit_prodi(prodi_id):
    _, err = require_admin()
    if err:
        return err

    prodi = KurikulumProdi.query.get(prodi_id)
    if not prodi:
        return jsonify({"error": "Prodi tidak ditemukan"}), 404

    data = request.get_json(silent=True) or {}

    if "nama_prodi" in data:
        nama_baru = (data["nama_prodi"] or "").strip()
        if not nama_baru:
            return jsonify({"error": "nama_prodi tidak boleh kosong"}), 400
        existing = KurikulumProdi.query.filter_by(nama_prodi=nama_baru).first()
        if existing and existing.id != prodi_id:
            return jsonify({"error": f"Program studi '{nama_baru}' sudah ada"}), 400
        prodi.nama_prodi = nama_baru
    if "total_semester" in data:
        prodi.total_semester = int(data["total_semester"])
    if "sks_lulus" in data:
        prodi.sks_lulus = int(data["sks_lulus"])
    if "syarat_sidang_sks" in data:
        prodi.syarat_sidang_sks = int(data["syarat_sidang_sks"])
    if "is_active" in data:
        prodi.is_active = bool(data["is_active"])

    db.session.commit()
    reload_kurikulum()

    return jsonify({"message": "Prodi berhasil diperbarui", "prodi": prodi.to_dict()}), 200


# Import XLSX
def _parse_semester_label(value) -> int | None:
    if not value or not isinstance(value, str):
        return None
    m = re.match(r"semester\s*(\d+)", value.strip(), re.IGNORECASE)
    return int(m.group(1)) if m else None


@admin_bp.route("/import-xlsx", methods=["POST"])
def import_xlsx():
    _, err = require_admin()
    if err:
        return err

    if "file" not in request.files:
        return jsonify({"error": "File tidak ditemukan dalam request."}), 400

    file = request.files["file"]
    prodi_id = request.form.get("prodi_id")

    if not file.filename or not file.filename.endswith(".xlsx"):
        return jsonify({"error": "File harus berformat .xlsx"}), 400

    if not prodi_id:
        return jsonify({"error": "prodi_id wajib diisi."}), 400

    prodi = KurikulumProdi.query.get(int(prodi_id))
    if not prodi:
        return jsonify({"error": "Program studi tidak ditemukan."}), 404

    try:
        wb = openpyxl.load_workbook(io.BytesIO(file.read()), data_only=True)
        ws = wb.active
    except Exception:
        return jsonify({"error": "File XLSX tidak dapat dibaca. Pastikan format file benar."}), 400

    current_semester = 0
    matakuliah = []

    for row in ws.iter_rows(values_only=True):
        if all(v is None for v in row):
            continue

        sem = _parse_semester_label(row[0])
        if sem is not None:
            current_semester = sem
            continue

        # Lewati baris header (kolom 0 = "No")
        if row[0] and str(row[0]).strip().lower() == "no":
            continue

        no, kode, nama, sks, prasyarat, keterangan = (
            row[0], row[1], row[2], row[3],
            row[4] if len(row) > 4 else None,
            row[5] if len(row) > 5 else None,
        )

        if not isinstance(no, int) or not nama:
            continue
        if not isinstance(sks, (int, float)) or sks <= 0:
            continue

        matakuliah.append({
            "no": int(no),
            "kode": str(kode).strip() if kode else "",
            "nama": str(nama).strip(),
            "sks": int(sks),
            "semester": current_semester,
            "prasyarat": str(prasyarat).strip() if prasyarat else None,
            "keterangan": str(keterangan).strip() if keterangan else None,
        })

    if not matakuliah:
        return jsonify({"error": "Tidak ada data mata kuliah valid yang ditemukan di file."}), 400

    # Hapus matkul lama utk masukkan matkul  baru
    MataKuliahKurikulum.query.filter_by(prodi_id=prodi.id).delete()

    for urutan, mk in enumerate(matakuliah):
        db.session.add(MataKuliahKurikulum(
            prodi_id=prodi.id,
            kode=mk["kode"],
            nama=mk["nama"],
            sks=mk["sks"],
            semester=mk["semester"],
            keterangan=mk["keterangan"],
            prasyarat=mk["prasyarat"],
            urutan=urutan,
        ))

    db.session.commit()
    reload_kurikulum()

    total_sks = sum(mk["sks"] for mk in matakuliah)

    return jsonify({
        "message": f"Kurikulum {prodi.nama_prodi} berhasil diimport",
        "total_mk": len(matakuliah),
        "total_sks": total_sks,
    }), 200


# Create Read Delete Update informasi baru dari admin
@admin_bp.route("/pengetahuan", methods=["GET"])
def list_pengetahuan():
    _, err = require_admin()
    if err:
        return err

    semua = InformasiChatbot.query.order_by(InformasiChatbot.id).all()

    return jsonify({
        "pengetahuan": [p.to_dict() for p in semua],
        "total": len(semua),
    }), 200


@admin_bp.route("/pengetahuan", methods=["POST"])
def tambah_pengetahuan():
    _, err = require_admin()
    if err:
        return err

    data   = request.get_json(silent=True) or {}
    judul  = (data.get("judul") or "").strip()
    konten = (data.get("konten") or "").strip()

    if not judul:
        return jsonify({"error": "Judul wajib diisi."}), 400
    if not konten:
        return jsonify({"error": "Konten wajib diisi."}), 400

    p = InformasiChatbot(
        judul=judul,
        konten=konten,
        kategori=(data.get("kategori") or "").strip() or None,
        is_active=bool(data.get("is_active", True)),
    )
    db.session.add(p)
    db.session.commit()

    return jsonify({"message": "Informasi berhasil ditambahkan", "pengetahuan": p.to_dict()}), 201


@admin_bp.route("/pengetahuan/<int:p_id>", methods=["PUT"])
def edit_pengetahuan(p_id):
    _, err = require_admin()
    if err:
        return err

    p = InformasiChatbot.query.get(p_id)
    if not p:
        return jsonify({"error": "Informasi tidak ditemukan."}), 404

    data = request.get_json(silent=True) or {}

    if "judul" in data:
        p.judul = (data["judul"] or "").strip()
    if "konten" in data:
        p.konten = (data["konten"] or "").strip()
    if "kategori" in data:
        p.kategori = (data["kategori"] or "").strip() or None
    if "is_active" in data:
        p.is_active = bool(data["is_active"])

    db.session.commit()

    return jsonify({"message": "Informasi berhasil diperbarui", "pengetahuan": p.to_dict()}), 200


@admin_bp.route("/pengetahuan/<int:p_id>", methods=["DELETE"])
def hapus_pengetahuan(p_id):
    _, err = require_admin()
    if err:
        return err

    p = InformasiChatbot.query.get(p_id)
    if not p:
        return jsonify({"error": "Informasi tidak ditemukan."}), 404

    db.session.delete(p)
    db.session.commit()

    return jsonify({"message": "Pengetahuan berhasil dihapus."}), 200