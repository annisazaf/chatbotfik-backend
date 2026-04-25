from pathlib import Path
import json

from src.ocr.khs_extractor import extract_khs_from_pdf
from src.curriculum.curriculum_loaderb4 import load_all_kurikulum
from src.analysis.progress_analyzer import analyze_to_json

BASE_DIR      = Path(__file__).parent
KHS_DIR       = BASE_DIR / "data" / "khs"
KURIKULUM_DIR = BASE_DIR / "data" / "kurikulum"
OUTPUT_DIR    = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

KHS_FILES = [
    "ContohKHSD3SistemInformasi.pdf",
    "ContohKHSS1Informatika.pdf",
    "ContohKHSS1SainsData.pdf",
    "ContohKHSS1SistemInformasi.pdf",
]


if __name__ == "__main__":

    # STEP 1 — Load semua kurikulum
    print("\n" + "=" * 50)
    print("  STEP 1 — Load Kurikulum")
    print("=" * 50)
    semua_kurikulum = load_all_kurikulum(KURIKULUM_DIR)

    # STEP 2 — OCR + Analisis tiap KHS
    print("\n" + "=" * 50)
    print("  STEP 2 — OCR & Analisis KHS")
    print("=" * 50)

    for filename in KHS_FILES:
        pdf_path = KHS_DIR / filename
        if not pdf_path.exists():
            print(f"[SKIP] {filename}")
            continue

        print(f"\n Membaca : {filename}")
        try:
            khs = extract_khs_from_pdf(pdf_path)
            print(f"   Nama   : {khs.nama_mahasiswa}")
            print(f"   Prodi  : {khs.program_studi}")
            print(f"   IPK    : {khs.ipk}")

            # Ambil kurikulum sesuai prodi mahasiswa
            kurikulum = semua_kurikulum.get(khs.program_studi)
            if not kurikulum:
                print(f"   [SKIP] Kurikulum untuk '{khs.program_studi}' tidak ditemukan")
                continue

            # Analisis
            out_path = OUTPUT_DIR / filename.replace(".pdf", "_analisis.json")
            result   = analyze_to_json(khs, kurikulum, out_path)

            # Preview ringkasan
            data = json.loads(result)
            print(f"   MK Lulus  : {data['jumlah_mk_lulus']}")
            print(f"   MK Belum  : {data['jumlah_mk_belum']}")
            print(f"   SKS Tempuh: {data['sks_sudah_tempuh']} / {data['total_sks_kurikulum']}")
            print(f"   SKS Sisa  : {data['sks_belum_tempuh']}")

        except Exception as e:
            print(f"   [ERROR] {e}")

    print("\n Semua selesai. Cek folder output/")