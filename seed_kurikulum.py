"""
Script sekali-pakai untuk migrasi data kurikulum dari file XLSX
yang sudah ada ke tabel database (kurikulum_prodi + mata_kuliah_kurikulum).
"""

import sys
from pathlib import Path

# Pastikan src bisa diimport
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from app import app, db
from src.models import KurikulumProdi, MataKuliahKurikulum
from src.curriculum.curriculum_loader import load_all_kurikulum
from src.rules.academic_rules import ATURAN_PRODI, PEMINATAN_PRODI

KURIKULUM_DIR = BASE_DIR / "data" / "kurikulum"


def seed():
    print("\n" + "=" * 55)
    print("  SEED KURIKULUM: XLSX → PostgreSQL")
    print("=" * 55)

    # Load semua kurikulum dari XLSX (pakai loader lama yang sudah ada)
    semua_kurikulum = load_all_kurikulum(KURIKULUM_DIR)

    with app.app_context():
        seeded = 0
        skipped = 0

        for nama_prodi, kurikulum in semua_kurikulum.items():
            # Cek apakah prodi sudah ada di DB
            existing = KurikulumProdi.query.filter_by(nama_prodi=nama_prodi).first()
            if existing:
                print(f"\n  [SKIP] '{nama_prodi}' sudah ada di DB (id={existing.id})")
                skipped += 1
                continue

            print(f"\n  Menyimpan: {nama_prodi}")
            print(f"    MK      : {len(kurikulum.matakuliah)} mata kuliah")
            print(f"    Total   : {kurikulum.total_sks} SKS")

            # Ambil aturan akademik dari rules (hardcode lama)
            aturan = ATURAN_PRODI.get(nama_prodi, {})
            peminatan = PEMINATAN_PRODI.get(nama_prodi, {})

            # Susun peminatan_config
            peminatan_config = None
            if peminatan:
                jalur = peminatan.get("jalur", {})
                peminatan_config = {
                    "harus_konsisten":   peminatan.get("harus_konsisten", False),
                    "min_mk_per_jalur":  peminatan.get("min_mk_per_jalur", 0),
                    "jalur":             jalur if isinstance(jalur, dict) else {},
                    "keterangan":        peminatan.get("keterangan", ""),
                }

            # Buat record prodi
            prodi_record = KurikulumProdi(
                nama_prodi        = nama_prodi,
                total_semester    = aturan.get("total_semester", 8),
                sks_lulus         = aturan.get("sks_lulus", 144),
                syarat_sidang_sks = aturan.get("syarat_sidang_sks", 138),
                is_active         = True,
                peminatan_config  = peminatan_config,
            )
            db.session.add(prodi_record)
            db.session.flush()  # dapat id sebelum commit

            # Masukkan semua mata kuliah
            for urutan, mk in enumerate(kurikulum.matakuliah):
                mk_record = MataKuliahKurikulum(
                    prodi_id   = prodi_record.id,
                    kode       = mk.kode or "",
                    nama       = mk.nama,
                    sks        = mk.sks,
                    semester   = mk.semester,
                    keterangan = mk.keterangan,
                    prasyarat  = mk.prasyarat,
                    urutan     = urutan,
                )
                db.session.add(mk_record)

            print(f"    → Tersimpan dengan id={prodi_record.id}")
            seeded += 1

        db.session.commit()

        print("\n" + "─" * 55)
        print(f"  Selesai! {seeded} prodi diimpor, {skipped} prodi dilewati.")
        print("─" * 55)

        # Verifikasi
        print("\n  Verifikasi isi DB:")
        semua_prodi = KurikulumProdi.query.all()
        for p in semua_prodi:
            total_sks = sum(mk.sks for mk in p.mata_kuliah)
            print(f"  • [{p.id}] {p.nama_prodi} — {len(p.mata_kuliah)} MK, {total_sks} SKS, active={p.is_active}")


if __name__ == "__main__":
    seed()
