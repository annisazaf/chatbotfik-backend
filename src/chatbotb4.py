"""
Chatbot KHS dengan DeepSeek API
Lokasi: src/chatbot.py


import os
from pathlib import Path
from dataclasses import asdict
from openai import OpenAI
from dotenv import load_dotenv

from src.ocr.khs_extractor import extract_khs_from_pdf
from src.curriculum.curriculum_loaderb4 import load_all_kurikulum
from src.analysis.progress_analyzer import analyze_progress

load_dotenv()

# ─────────────────────────────────────────────
# SETUP CLIENT
# ─────────────────────────────────────────────

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# ─────────────────────────────────────────────
# LOAD KURIKULUM SEKALI SAAT STARTUP
# ─────────────────────────────────────────────

BASE_DIR        = Path(__file__).parent.parent
KURIKULUM_DIR   = BASE_DIR / "data" / "kurikulum"
SEMUA_KURIKULUM = load_all_kurikulum(KURIKULUM_DIR)


# ─────────────────────────────────────────────
# PROSES PDF KHS
# ─────────────────────────────────────────────

def proses_khs(pdf_path: str) -> dict:
    """Baca PDF KHS, analisis, kembalikan dict hasil analisis."""
    khs = extract_khs_from_pdf(pdf_path)
    kurikulum = SEMUA_KURIKULUM.get(khs.program_studi)
    if not kurikulum:
        raise ValueError(
            f"Kurikulum untuk prodi '{khs.program_studi}' tidak ditemukan.\n"
            f"Prodi tersedia: {', '.join(SEMUA_KURIKULUM.keys())}"
        )
    hasil = analyze_progress(khs, kurikulum)
    return asdict(hasil)


# ─────────────────────────────────────────────
# BUILD SYSTEM PROMPT
# ─────────────────────────────────────────────

def build_system_prompt(hasil: dict) -> str:
    persen    = (hasil['sks_sudah_tempuh'] / hasil['total_sks_kurikulum'] * 100) \
                 if hasil['total_sks_kurikulum'] else 0
    bisa_sid  = hasil['bisa_sidang']
    kurang_sid = hasil['syarat_sidang_sks'] - hasil['sks_sudah_tempuh']

    mk_lulus_text = "\n".join([
        f"  - {mk['nama']} | Nilai: {mk['nilai'] or '-'} | HM: {mk['HM']} "
        f"| {mk['SKS']} SKS | Sem.{mk['semester_kurikulum']} | [{mk.get('keterangan','-')}]"
        for mk in hasil['mk_sudah_lulus']
    ])

    mk_belum_text = "\n".join([
        f"  - {mk['nama']} | {mk['sks']} SKS | Sem.{mk['semester_kurikulum']} "
        f"| [{mk.get('keterangan','-')}]"
        for mk in hasil['mk_belum_diambil']
    ])

    peminatan_text = "\n".join([
        f"  - {p['jalur_kode']} ({p['jalur_nama']}): "
        f"{p['jumlah_mk']}/{p['min_required']} MK "
        f"{'✅' if p['sudah_cukup'] else '❌'}"
        for p in hasil.get('peminatan_info', [])
    ]) or "  (tidak ada data peminatan)"

    try:
        nim_akhir = int(str(hasil['nim'])[-1])
        nim_jenis = 'ganjil' if nim_akhir % 2 != 0 else 'genap'
    except (ValueError, IndexError):
        nim_jenis = '-'

    prompt = f"""Kamu adalah asisten akademik chatbot bernama FIKA untuk mahasiswa Fakultas Ilmu Komputer UPN "Veteran" Jakarta.
Tugasmu membantu mahasiswa memahami progress studi mereka. Jawab ramah, jelas, dalam Bahasa Indonesia.

=== DATA MAHASISWA ===
Nama          : {hasil['nama_mahasiswa']}
NIM           : {hasil['nim']}
Program Studi : {hasil['program_studi']}
IPK           : {hasil['ipk']:.2f}
IPS Terakhir  : {hasil['ips']:.2f}
Total Semester: {hasil['total_semester']} semester
Semester MBKM : Semester {hasil['semester_mbkm']} (NIM {nim_jenis})

=== PROGRESS SKS ===
SKS Sudah Tempuh    : {hasil['sks_sudah_tempuh']} SKS
SKS Wajib Lulus     : {hasil['sks_wajib_lulus']} SKS
Total SKS Kurikulum : {hasil['total_sks_kurikulum']} SKS
SKS Belum Tempuh    : {hasil['sks_belum_tempuh']} SKS
Progress            : {persen:.1f}%

=== SYARAT SIDANG ===
Minimal SKS Sidang  : {hasil['syarat_sidang_sks']} SKS
Status              : {"✅ Memenuhi syarat SKS sidang" if bisa_sid else f"❌ Belum memenuhi, kurang {kurang_sid} SKS"}

=== MATAKULIAH ===
MK Lulus : {hasil['jumlah_mk_lulus']} mata kuliah
MK Belum : {hasil['jumlah_mk_belum']} mata kuliah

=== ANALISIS PEMINATAN ===
{hasil.get('peminatan_pesan', '-')}
Detail per jalur:
{peminatan_text}

=== JENIS MATAKULIAH ===
- MKWU      : Mata Kuliah Wajib Universitas (wajib semua mahasiswa UPN)
- MKPS      : Mata Kuliah Wajib Fakultas & Prodi (wajib semua mahasiswa FIK)
- MBKM      : Merdeka Belajar Kampus Merdeka (kegiatan di luar prodi, maks 3 semester)
- PLPS      : Pembelajaran di Luar Program Studi (MK dari prodi/fakultas lain)
- Peminatan : Sesuai jalur peminatan yang dipilih (harus konsisten 1 jalur, min 3 MK)
- Pilihan   : Bebas dipilih dari daftar yang tersedia

=== DAFTAR MK SUDAH LULUS ===
{mk_lulus_text or "  (tidak ada data)"}

=== DAFTAR MK BELUM DIAMBIL ===
{mk_belum_text or "  (semua MK sudah diambil)"}

Gunakan semua data di atas untuk menjawab pertanyaan mahasiswa secara akurat.
"""
    return prompt


# ─────────────────────────────────────────────
# CHAT DENGAN DEEPSEEK
# ─────────────────────────────────────────────

def chat(pesan: str, history: list, system_prompt: str, max_tokens: int = 1024) -> str:
    messages = [{"role": "system", "content": system_prompt}]
    messages += history
    messages.append({"role": "user", "content": pesan})

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        max_tokens=max_tokens,
        temperature=0.7,
    )

    return response.choices[0].message.content"""