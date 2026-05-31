import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

import openpyxl

@dataclass
class MataKuliahKurikulum:
    no: int
    kode: str
    nama: str
    sks: int
    prasyarat: Optional[str]
    keterangan: Optional[str]
    semester: int


@dataclass
class Kurikulum:
    program_studi: str
    total_sks: int
    matakuliah: list = field(default_factory=list)


# Load dari database (production)
def load_kurikulum_from_db(nama_prodi: str) -> Optional[Kurikulum]:
    from src.models import KurikulumProdi

    prodi = KurikulumProdi.query.filter_by(nama_prodi=nama_prodi, is_active=True).first()
    if not prodi:
        return None

    kurikulum = Kurikulum(program_studi=prodi.nama_prodi, total_sks=0)
    for mk in prodi.mata_kuliah:
        kurikulum.matakuliah.append(MataKuliahKurikulum(
            no = mk.urutan,
            kode = mk.kode or "",
            nama = mk.nama,
            sks = mk.sks,
            prasyarat = mk.prasyarat,
            keterangan = mk.keterangan,
            semester = mk.semester,
        ))
        kurikulum.total_sks += mk.sks

    return kurikulum


def load_all_kurikulum_from_db() -> dict:
    """Baca semua kurikulum aktif dari DB. Return {"S1 Informatika": Kurikulum, ...}"""
    from src.models import KurikulumProdi

    result = {}
    for prodi in KurikulumProdi.query.filter_by(is_active=True).all():
        kurikulum = Kurikulum(program_studi=prodi.nama_prodi, total_sks=0)
        for mk in prodi.mata_kuliah:
            kurikulum.matakuliah.append(MataKuliahKurikulum(
                no = mk.urutan,
                kode = mk.kode or "",
                nama = mk.nama,
                sks = mk.sks,
                prasyarat = mk.prasyarat,
                keterangan = mk.keterangan,
                semester = mk.semester,
            ))
            kurikulum.total_sks += mk.sks
        result[prodi.nama_prodi] = kurikulum

    return result


# Load data dari xlsx (hanya untuk seed_kurikulum.py)
FILE_TO_PRODI = {
    "KurikulumD3SistemInformasi.xlsx": "D3 Sistem Informasi",
    "KurikulumS1Informatika.xlsx":     "S1 Informatika",
    "KurikulumS1SainsData.xlsx":       "S1 Sains Data",
    "KurikulumS1SistemInformasi.xlsx": "S1 Sistem Informasi",
}


def detect_prodi_from_filename(filename: str) -> str:
    return FILE_TO_PRODI.get(Path(filename).name, Path(filename).stem)


def parse_semester_label(value) -> Optional[int]:
    if not value or not isinstance(value, str):
        return None
    m = re.match(r"semester\s*(\d+)", value.strip(), re.IGNORECASE)
    return int(m.group(1)) if m else None


def is_header_row(row: tuple) -> bool:
    if not row[0]:
        return False
    return str(row[0]).strip().lower() == "no"


def load_kurikulum(xlsx_path) -> Kurikulum:
    """Baca satu file XLSX, hanya dipakai seed_kurikulum.py"""
    xlsx_path = Path(xlsx_path)
    if not xlsx_path.exists():
        raise FileNotFoundError(f"File tidak ditemukan: {xlsx_path}")

    prodi = detect_prodi_from_filename(xlsx_path.name)
    wb    = openpyxl.load_workbook(xlsx_path, data_only=True)
    ws    = wb.active

    kurikulum        = Kurikulum(program_studi=prodi, total_sks=0)
    current_semester = 0

    for row in ws.iter_rows(values_only=True):
        if all(v is None for v in row):
            continue
        sem = parse_semester_label(row[0])
        if sem is not None:
            current_semester = sem
            continue
        if is_header_row(row):
            continue

        no, kode, nama, sks, prasyarat, keterangan = (
            row[0], row[1], row[2], row[3], row[4], row[5]
        )
        if not isinstance(no, int) or not nama:
            continue
        if not isinstance(sks, int) or sks <= 0:
            continue

        kurikulum.matakuliah.append(MataKuliahKurikulum(
            no = no,
            kode = str(kode).strip() if kode else "",
            nama = str(nama).strip(),
            sks = sks,
            prasyarat = str(prasyarat).strip() if prasyarat else None,
            keterangan = str(keterangan).strip() if keterangan else None,
            semester = current_semester,
        ))
        kurikulum.total_sks += sks

    return kurikulum


def load_all_kurikulum(kurikulum_dir) -> dict:
    """Baca semua XLSX di folder, hanya dipakai seed_kurikulum.py"""
    kurikulum_dir = Path(kurikulum_dir)
    result = {}
    for xlsx_file in sorted(kurikulum_dir.glob("*.xlsx")):
        try:
            k = load_kurikulum(xlsx_file)
            result[k.program_studi] = k
            print(f"  Loaded XLSX: {k.program_studi} — {len(k.matakuliah)} MK, {k.total_sks} SKS")
        except Exception as e:
            print(f"  [ERROR] {xlsx_file.name}: {e}")
    return result

"""
Cara load kurikulum:
1. load_all_kurikulum_from_db() - baca dari PostgreSQL (production)
2. load_kurikulum_from_db() - baca satu prodi dari DB
3. load_kurikulum() - baca dari XLSX (hanya seed_kurikulum.py)
4. load_all_kurikulum() - baca semua XLSX (hanya seed_kurikulum.py)
"""