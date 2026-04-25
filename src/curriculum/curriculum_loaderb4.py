"""
Curriculum Loader
Membaca file XLSX kurikulum per prodi dan mengubahnya menjadi struktur data terorganisir.

Lokasi: khs-analyzer/src/curriculum/curriculum_loader.py


import re
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional

import openpyxl


# ─────────────────────────────────────────────
# DATA CLASSES
# ─────────────────────────────────────────────

@dataclass
class MataKuliahKurikulum:
    no: int
    kode: str
    nama: str
    sks: int
    prasyarat: Optional[str]
    keterangan: Optional[str]   # MKWU, MKPS, MKPP, dll.
    semester: int               # 1, 2, 3, dst.


@dataclass
class Kurikulum:
    program_studi: str
    total_sks: int
    matakuliah: list = field(default_factory=list)   # list of MataKuliahKurikulum


# ─────────────────────────────────────────────
# MAPPING NAMA FILE → PRODI
# ─────────────────────────────────────────────

FILE_TO_PRODI = {
    "KurikulumD3SistemInformasi.xlsx": "D3 Sistem Informasi",
    "KurikulumS1Informatika.xlsx":     "S1 Informatika",
    "KurikulumS1SainsData.xlsx":       "S1 Sains Data",
    "KurikulumS1SistemInformasi.xlsx": "S1 Sistem Informasi",
}


def detect_prodi_from_filename(filename: str) -> str:
    """Deteksi nama prodi dari nama file."""
    return FILE_TO_PRODI.get(Path(filename).name, Path(filename).stem)


# ─────────────────────────────────────────────
# PARSER
# ─────────────────────────────────────────────

def parse_semester_label(value) -> Optional[int]:
    """
    Deteksi baris label semester.
    Contoh: 'Semester 1' → 1, 'Semester 3' → 3
    """
    if not value or not isinstance(value, str):
        return None
    m = re.match(r"semester\s*(\d+)", value.strip(), re.IGNORECASE)
    return int(m.group(1)) if m else None


def is_header_row(row: tuple) -> bool:
    """Deteksi baris header kolom (No, Kode, Mata Kuliah, ...)."""
    if not row[0]:
        return False
    return str(row[0]).strip().lower() == "no"


def load_kurikulum(xlsx_path) -> Kurikulum:
    """
    Baca satu file XLSX kurikulum dan kembalikan objek Kurikulum.

    Parameters
    ----------
    xlsx_path : str | Path

    Returns
    -------
    Kurikulum
    
    xlsx_path = Path(xlsx_path)
    if not xlsx_path.exists():
        raise FileNotFoundError(f"File tidak ditemukan: {xlsx_path}")

    prodi = detect_prodi_from_filename(xlsx_path.name)
    wb    = openpyxl.load_workbook(xlsx_path, data_only=True)
    ws    = wb.active

    kurikulum = Kurikulum(program_studi=prodi, total_sks=0)

    current_semester = 0

    for row in ws.iter_rows(values_only=True):
        # Lewati baris kosong total
        if all(v is None for v in row):
            continue

        # Cek label semester (mis. "Semester 1")
        sem = parse_semester_label(row[0])
        if sem is not None:
            current_semester = sem
            continue

        # Lewati baris header kolom
        if is_header_row(row):
            continue

        # Parse baris matakuliah
        no          = row[0]
        kode        = row[1]
        nama        = row[2]
        sks         = row[3]
        prasyarat   = row[4]
        keterangan  = row[5]

        # Validasi: no harus integer dan nama harus ada
        if not isinstance(no, int) or not nama:
            continue
        if not isinstance(sks, int) or sks <= 0:
            continue

        mk = MataKuliahKurikulum(
            no          = no,
            kode        = str(kode).strip() if kode else "",
            nama        = str(nama).strip(),
            sks         = sks,
            prasyarat   = str(prasyarat).strip() if prasyarat else None,
            keterangan  = str(keterangan).strip() if keterangan else None,
            semester    = current_semester,
        )

        kurikulum.matakuliah.append(mk)
        kurikulum.total_sks += sks

    return kurikulum


def load_kurikulum_to_json(xlsx_path, output_path=None) -> str:
    """Baca XLSX dan kembalikan / simpan sebagai JSON."""
    data     = asdict(load_kurikulum(xlsx_path))
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    if output_path:
        Path(output_path).write_text(json_str, encoding="utf-8")
        print(f"Disimpan ke: {output_path}")
    return json_str


def load_all_kurikulum(kurikulum_dir) -> dict:
    """
    Baca semua file XLSX kurikulum dalam satu folder.
    Kembalikan dict dengan key = nama prodi.

    Returns
    -------
    {
        "D3 Sistem Informasi": Kurikulum,
        "S1 Informatika":      Kurikulum,
        ...
    }
    """
    kurikulum_dir = Path(kurikulum_dir)
    result = {}

    for xlsx_file in sorted(kurikulum_dir.glob("*.xlsx")):
        try:
            k = load_kurikulum(xlsx_file)
            result[k.program_studi] = k
            print(f"  Loaded: {k.program_studi} — {len(k.matakuliah)} MK, {k.total_sks} SKS")
        except Exception as e:
            print(f"  [ERROR] {xlsx_file.name}: {e}")

    return result


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python curriculum_loader.py <kurikulum.xlsx> [output.json]")
        sys.exit(1)
    result = load_kurikulum_to_json(
        sys.argv[1],
        sys.argv[2] if len(sys.argv) > 2 else None
    )
    if len(sys.argv) < 3:
        print(result)
"""
