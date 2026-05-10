import re
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional

import pdfplumber


@dataclass
class MataKuliah:
    nama: str
    nilai: Optional[str]
    HM: Optional[float]
    SKS: int
    M: Optional[float]


@dataclass
class KHSData:
    nama_mahasiswa: str
    nim: str
    program_studi: str
    ipk: float
    ips: float
    sks_kumulatif: int
    sks_semester_lalu: int
    batas_ambil_sks: int
    matakuliah: list = field(default_factory=list)
    source_file: str = ""


# Normalisasi prodi
PRODI_ALIASES = {
    "sistem informasi d-iii":"D3 Sistem Informasi",
    "sistem informasi s.1":"S1 Sistem Informasi",
    "sains data s.1":"S1 Sains Data",
    "informatika s.1":"S1 Informatika",
}


def normalize_prodi(raw: str) -> str:
    key = raw.strip().lower()
    for alias, canonical in PRODI_ALIASES.items():
        if alias in key:
            return canonical
    return raw.strip().title()


def parse_float(val) -> Optional[float]:
    try:
        return float(str(val).strip().replace(",", "."))
    except (ValueError, AttributeError):
        return None


def parse_int(val) -> Optional[int]:
    try:
        return int(str(val).strip())
    except (ValueError, AttributeError):
        return None


# Ekstrak header
def extract_header_info(text: str) -> dict:
    info = {}

    m = re.search(r"Program Studi\s*[:\-]\s*(.+)", text, re.IGNORECASE)
    if m:
        info["program_studi"] = normalize_prodi(m.group(1).strip())

    m = re.search(r"Nama Mahasiswa\s*[:\-]\s*(.+)", text, re.IGNORECASE)
    if m:
        info["nama_mahasiswa"] = m.group(1).strip()

    m = re.search(r"NIM\s*[:\-]\s*(\d+)", text, re.IGNORECASE)
    if m:
        info["nim"] = m.group(1).strip()

    m = re.search(
        r"Prestasi Kumulatif\s*[:\-]\s*(\d+)\s*[,.]?\s*IPK[.\s]*(\d+[.,]\d+)",
        text, re.IGNORECASE
    )
    if m:
        info["sks_kumulatif"] = int(m.group(1))
        info["ipk"] = parse_float(m.group(2))

    m = re.search(
        r"Sks Semester Lalu\s*[:\-]\s*(\d+)\s*[,.]?\s*IPS[.\s]*(\d+[.,]\d+)",
        text, re.IGNORECASE
    )
    if m:
        info["sks_semester_lalu"] = int(m.group(1))
        info["ips"] = parse_float(m.group(2))

    m = re.search(r"Batas Ambil Sks\s*[:\-]\s*(\d+)", text, re.IGNORECASE)
    if m:
        info["batas_ambil_sks"] = int(m.group(1))

    return info


# Parse baris matkul
def detect_semester_label(line: str) -> bool:
    """Deteksi baris label semester agar dilewati."""
    return bool(re.match(
        r"^\s*SEMESTER\s+(I{1,3}V?|VI{0,3}|VIII?)\s*$",
        line.strip(), re.IGNORECASE
    ))


MK_PATTERN = re.compile(
    r"^\s*(\d{1,3})" # nomor
    r"(?:\s+\[[\s]*\])?" # opsional [ ] atau []
    r"\s+(.+?)" # nama matakuliah
    r"(?:\s+(A[+-]?|B[+-]?|C[+-]?|D|E))?" # opsional grade huruf
    r"\s+(\d+[.,]\d{2})" # grade angka (HM)
    r"\s+(\d{1,2})" # SKS
    r"\s+(\d+[.,]\d{2})" # mutu (M)
    r"(?:\s+\*)?\s*$" # opsional *
)


def parse_single_line(line: str) -> Optional[MataKuliah]:
    """Hanya kembalikan data jika HM > 0 (sudah diambil mahasiswa)"""
    line = line.strip()
    if not line:
        return None

    m = MK_PATTERN.match(line)
    if not m:
        return None

    nama    = m.group(2).strip()
    nama    = re.sub(r"\s*\(.*?\)\s*$", "", nama).strip()  # hapus keterangan peminatan
    grade_h = (m.group(3) or "").strip() or None
    grade_a = parse_float(m.group(4))
    sks     = parse_int(m.group(5)) or 0
    mutu    = parse_float(m.group(6))

    # Filter lewati matakuliah yang belum diambil
    if not grade_a or grade_a == 0.0:
        return None

    return MataKuliah(
        nama=nama,
        nilai=grade_h,
        HM=grade_a,
        SKS=sks,
        M=mutu if mutu and mutu > 0 else None,
    )


# Crop halaman kiri dan kanan
def extract_lines_from_page(page) -> list:
   
    width  = page.width
    height = page.height

    left_text  = page.crop((0,            0, width * 0.50, height)).extract_text() or ""
    right_text = page.crop((width * 0.50, 0, width,        height)).extract_text() or ""

    return left_text.splitlines() + right_text.splitlines()


# Main
def extract_khs_from_pdf(pdf_path) -> KHSData:
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"File tidak ditemukan: {pdf_path}")

    all_lines = []
    full_text = ""

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            full_text += "\n" + (page.extract_text() or "")
            all_lines.extend(extract_lines_from_page(page))

    header = extract_header_info(full_text)

    khs = KHSData(
        nama_mahasiswa = header.get("nama_mahasiswa", "UNKNOWN"),
        nim = header.get("nim", "UNKNOWN"),
        program_studi = header.get("program_studi", "UNKNOWN"),
        ipk = header.get("ipk", 0.0),
        ips = header.get("ips", 0.0),
        sks_kumulatif = header.get("sks_kumulatif", 0),
        sks_semester_lalu = header.get("sks_semester_lalu", 0),
        batas_ambil_sks = header.get("batas_ambil_sks", 0),
        source_file = pdf_path.name,
    )

    seen = set()  # deduplikasi berdasarkan nama matakuliah

    for line in all_lines:
        if detect_semester_label(line):
            continue

        mk = parse_single_line(line)
        if mk:
            key = mk.nama.lower()
            if key not in seen:
                seen.add(key)
                khs.matakuliah.append(mk)

    return khs


def extract_khs_to_json(pdf_path, output_path=None) -> str:
    data = asdict(extract_khs_from_pdf(pdf_path))
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    if output_path:
        Path(output_path).write_text(json_str, encoding="utf-8")
        print(f"Disimpan ke: {output_path}")
    return json_str


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python khs_extractor.py <khs.pdf> [output.json]")
        sys.exit(1)
    result = extract_khs_to_json(
        sys.argv[1],
        sys.argv[2] if len(sys.argv) > 2 else None
    )
    if len(sys.argv) < 3:
        print(result)