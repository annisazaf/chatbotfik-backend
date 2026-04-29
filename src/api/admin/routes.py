from flask import Blueprint, request, jsonify, session
from src.api.auth.routes import db, User, get_nim_from_token
from src.models import KurikulumProdi, MataKuliahKurikulum
from src.chatbot import reload_kurikulum

admin_bp = Blueprint('admin', __name__)


# ─────────────────────────────────────────────
# HELPER: cek login admin (FIXED)
# ─────────────────────────────────────────────

def require_admin():
    """Cek admin dari session atau JWT."""
    nim = session.get("user_nim") or get_nim_from_token()

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
    user, err = require_admin()
    if err:
        return err
    return jsonify({"is_admin": True, "nim": user.nim, "nama": user.nama}), 200


# ─────────────────────────────────────────────
# CRUD PRODI
# ─────────────────────────────────────────────

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

# ─────────────────────────────────────────────
# LIST USERS (UNTUK PANEL ADMIN)
# ─────────────────────────────────────────────

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

# ─────────────────────────────────────────────
# UBAH ROLE USER
# ─────────────────────────────────────────────

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

# ─────────────────────────────────────────────
# LIST MK
# ─────────────────────────────────────────────

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


# ─────────────────────────────────────────────
# CRUD MK
# ─────────────────────────────────────────────

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