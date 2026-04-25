"""
Progress Analyzer — dengan aturan akademik per prodi
Lokasi: src/analysis/progress_analyzer.py
"""

import re
from dataclasses import dataclass, field, asdict
from typing import Optional
import json
from pathlib import Path

from src.ocr.khs_extractor import KHSData, extract_khs_from_pdf
from src.curriculum.curriculum_loader import Kurikulum, load_kurikulum
from src.rules.academic_rules import (
    ATURAN_PRODI, KETERANGAN_MK, PEMINATAN_PRODI, get_semester_mbkm
)


# ─────────────────────────────────────────────
# DATA CLASSES
# ─────────────────────────────────────────────

@dataclass
class MKSudahLulus:
    nama: str
    kode: str
    semester_kurikulum: int
    nilai: Optional[str]
    HM: Optional[float]
    SKS: int
    M: Optional[float]
    keterangan: Optional[str]  # MKWU, MKPS, MBKM, dst.


@dataclass
class MKBelumDiambil:
    nama: str
    kode: str
    semester_kurikulum: int
    sks: int
    keterangan: Optional[str]


@dataclass
class InfoPeminatan:
    jalur_kode: str            # CE, NE, SE, AU, AD, ES, DE, DA
    jalur_nama: str
    jumlah_mk: int
    sudah_cukup: bool          # >= min_mk_per_jalur
    min_required: int


@dataclass
class HasilAnalisis:
    # Info mahasiswa
    nama_mahasiswa: str
    nim: str
    program_studi: str
    ipk: float
    ips: float

    # SKS
    sks_kumulatif: int
    total_sks_kurikulum: int   # dari XLSX
    sks_wajib_lulus: int       # dari aturan prodi (108 / 144)
    sks_sudah_tempuh: int
    sks_belum_tempuh: int

    # MK
    jumlah_mk_lulus: int
    jumlah_mk_belum: int

    # Aturan prodi
    total_semester: int
    semester_mbkm: int
    syarat_sidang_sks: int
    bisa_sidang: bool

    # Peminatan
    peminatan_info: list = field(default_factory=list)
    peminatan_konsisten: bool = True
    peminatan_pesan: str = ""

    # Detail MK
    mk_sudah_lulus: list = field(default_factory=list)
    mk_belum_diambil: list = field(default_factory=list)


# ─────────────────────────────────────────────
# NORMALISASI & PENCOCOKAN NAMA
# ─────────────────────────────────────────────

def normalize_nama(nama: str) -> str:
    nama = nama.lower().strip()
    nama = re.sub(r"[/\(\)\[\]\*\+]", " ", nama)
    nama = re.sub(r"\s+", " ", nama)
    return nama.strip()


def is_match(nama_khs: str, nama_kurikulum: str) -> bool:
    a = normalize_nama(nama_khs)
    b = normalize_nama(nama_kurikulum)

    if a == b:
        return True
    if len(a) > 5 and len(b) > 5:
        if a in b or b in a:
            return True

    tokens_a = set(a.split())
    tokens_b = set(b.split())
    shorter  = tokens_a if len(tokens_a) <= len(tokens_b) else tokens_b
    longer   = tokens_b if len(tokens_a) <= len(tokens_b) else tokens_a
    if len(shorter) >= 2 and shorter.issubset(longer):
        return True

    return False


# ─────────────────────────────────────────────
# ANALISIS PEMINATAN
# ─────────────────────────────────────────────

def analisis_peminatan(mk_lulus: list, prodi: str) -> tuple:
    """
    Analisis jalur peminatan yang sudah diambil mahasiswa.
    Returns (list[InfoPeminatan], konsisten: bool, pesan: str)
    """
    aturan = PEMINATAN_PRODI.get(prodi)
    if not aturan or not aturan["harus_konsisten"]:
        return [], True, "Tidak ada aturan peminatan khusus untuk prodi ini."

    jalur_map  = aturan["jalur"]       # {"CE": "Cybersecurity", ...}
    min_mk     = aturan["min_mk_per_jalur"]

    # Hitung MK peminatan yang sudah lulus per jalur
    counter = {kode: 0 for kode in jalur_map}

    for mk in mk_lulus:
        ket = (mk.get("keterangan") or "").upper()
        for kode in jalur_map:
            # Kode peminatan muncul di field keterangan, misal "Peminatan CE.1", "CE.2"
            if kode in ket:
                counter[kode] += 1
                break

    # Buat list InfoPeminatan
    info_list = []
    for kode, nama in jalur_map.items():
        jumlah = counter[kode]
        info_list.append(InfoPeminatan(
            jalur_kode   = kode,
            jalur_nama   = nama,
            jumlah_mk    = jumlah,
            sudah_cukup  = jumlah >= min_mk,
            min_required = min_mk,
        ))

    # Cek konsistensi: hanya boleh 1 jalur yang diambil
    jalur_diambil = [kode for kode, jml in counter.items() if jml > 0]
    konsisten     = len(jalur_diambil) <= 1

    if not jalur_diambil:
        pesan = f"Belum mengambil mata kuliah peminatan apapun."
    elif not konsisten:
        pesan = (f"⚠️ Mengambil MK dari {len(jalur_diambil)} jalur peminatan berbeda "
                 f"({', '.join(jalur_diambil)}). Seharusnya hanya 1 jalur.")
    else:
        kode_aktif = jalur_diambil[0]
        jml_aktif  = counter[kode_aktif]
        nama_aktif = jalur_map[kode_aktif]
        if jml_aktif >= min_mk:
            pesan = (f"✅ Peminatan {nama_aktif} ({kode_aktif}): "
                     f"{jml_aktif} MK sudah diambil (syarat minimal {min_mk} MK).")
        else:
            kurang = min_mk - jml_aktif
            pesan  = (f"Peminatan {nama_aktif} ({kode_aktif}): "
                      f"{jml_aktif}/{min_mk} MK. Masih kurang {kurang} MK lagi.")

    return info_list, konsisten, pesan


# ─────────────────────────────────────────────
# MAIN ANALYZER
# ─────────────────────────────────────────────

def analyze_progress(khs: KHSData, kurikulum: Kurikulum) -> HasilAnalisis:
    aturan        = ATURAN_PRODI.get(khs.program_studi, {})
    sks_wajib     = aturan.get("sks_lulus", 144)
    total_sem     = aturan.get("total_semester", 8)
    syarat_sidang = aturan.get("syarat_sidang_sks", 138)
    sem_mbkm      = get_semester_mbkm(khs.nim)

    mk_lulus  = []
    mk_belum  = []
    sks_tempuh = 0

    nama_lulus_khs = {normalize_nama(mk.nama): mk for mk in khs.matakuliah if mk.HM}

    for mk_kur in kurikulum.matakuliah:
        nama_kur_norm = normalize_nama(mk_kur.nama)

        matched_mk = None
        for nama_khs_norm, mk_khs in nama_lulus_khs.items():
            if is_match(nama_khs_norm, nama_kur_norm):
                matched_mk = mk_khs
                break

        if matched_mk:
            mk_lulus.append(MKSudahLulus(
                nama               = mk_kur.nama,
                kode               = mk_kur.kode,
                semester_kurikulum = mk_kur.semester,
                nilai              = matched_mk.nilai,
                HM                 = matched_mk.HM,
                SKS                = mk_kur.sks,
                M                  = matched_mk.M,
                keterangan         = mk_kur.keterangan,
            ))
            sks_tempuh += mk_kur.sks
        else:
            mk_belum.append(MKBelumDiambil(
                nama               = mk_kur.nama,
                kode               = mk_kur.kode,
                semester_kurikulum = mk_kur.semester,
                sks                = mk_kur.sks,
                keterangan         = mk_kur.keterangan,
            ))

    sks_belum = kurikulum.total_sks - sks_tempuh
    bisa_sidang = sks_tempuh >= syarat_sidang

    # Analisis peminatan
    mk_lulus_dict = [asdict(m) for m in mk_lulus]
    peminatan_info, peminatan_konsisten, peminatan_pesan = analisis_peminatan(
        mk_lulus_dict, khs.program_studi
    )

    return HasilAnalisis(
        nama_mahasiswa       = khs.nama_mahasiswa,
        nim                  = khs.nim,
        program_studi        = khs.program_studi,
        ipk                  = khs.ipk,
        ips                  = khs.ips,
        sks_kumulatif        = khs.sks_kumulatif,
        total_sks_kurikulum  = kurikulum.total_sks,
        sks_wajib_lulus      = sks_wajib,
        sks_sudah_tempuh     = sks_tempuh,
        sks_belum_tempuh     = sks_belum,
        jumlah_mk_lulus      = len(mk_lulus),
        jumlah_mk_belum      = len(mk_belum),
        total_semester       = total_sem,
        semester_mbkm        = sem_mbkm,
        syarat_sidang_sks    = syarat_sidang,
        bisa_sidang          = bisa_sidang,
        peminatan_info       = [asdict(p) for p in peminatan_info],
        peminatan_konsisten  = peminatan_konsisten,
        peminatan_pesan      = peminatan_pesan,
        mk_sudah_lulus       = mk_lulus_dict,
        mk_belum_diambil     = [asdict(m) for m in mk_belum],
    )


def analyze_to_json(khs: KHSData, kurikulum: Kurikulum, output_path=None) -> str:
    hasil    = analyze_progress(khs, kurikulum)
    data     = asdict(hasil)
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    if output_path:
        Path(output_path).write_text(json_str, encoding="utf-8")
        print(f"Analisis disimpan ke: {output_path}")
    return json_str