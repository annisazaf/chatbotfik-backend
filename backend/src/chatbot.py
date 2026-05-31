import os
from pathlib import Path
from dataclasses import asdict
from openai import OpenAI
from dotenv import load_dotenv

from src.ocr.khs_extractor import extract_khs_from_pdf
from src.curriculum.curriculum_loader import load_all_kurikulum_from_db
from src.analysis.progress_analyzer import analyze_progress
from src.rules.academic_rules import ATURAN_SKPI

load_dotenv()

# Setup client
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# Load kurikulum sekali saat start
BASE_DIR        = Path(__file__).parent.parent
# Kurikulum dimuat dari DB saat pertama kali dibutuhkan
# agar tidak crash saat startup sebelum DB siap
_SEMUA_KURIKULUM = None


def get_semua_kurikulum() -> dict:
    """Lazy load kurikulum dari DB. Di-cache setelah load pertama"""
    global _SEMUA_KURIKULUM
    if _SEMUA_KURIKULUM is None:
        _SEMUA_KURIKULUM = load_all_kurikulum_from_db()
    return _SEMUA_KURIKULUM


def reload_kurikulum():
    """Paksa reload kurikulum dari DB (dipanggil setelah admin ubah kurikulum)"""
    global _SEMUA_KURIKULUM
    _SEMUA_KURIKULUM = load_all_kurikulum_from_db()
    return _SEMUA_KURIKULUM


# Proses PDF KHS
def proses_khs(pdf_path: str) -> dict:
    """Baca PDF KHS, analisis, kembalikan dict hasil analisis."""
    khs = extract_khs_from_pdf(pdf_path)
    kurikulum = get_semua_kurikulum().get(khs.program_studi)
    if not kurikulum:
        raise ValueError(
            f"Kurikulum untuk prodi '{khs.program_studi}' tidak ditemukan.\n"
            f"Prodi tersedia: {', '.join(get_semua_kurikulum().keys())}"
        )
    hasil = analyze_progress(khs, kurikulum)
    return asdict(hasil)


# Build System Prompt
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

    ATURAN FORMAT JAWABAN (WAJIB DIIKUTI):
    - Jawab RINGKAS dan PADAT. Fokus pada poin penting saja, hindari penjelasan panjang yang tidak perlu.
    - Gunakan tabel Markdown GFM untuk data yang bersifat perbandingan atau lebih dari 3 kolom. Format tabel yang BENAR:
    | Kolom 1 | Kolom 2 | Kolom 3 |
    |---------|---------|---------|
    | data    | data    | data    |
    - Jangan ulangi pertanyaan mahasiswa. Langsung ke jawaban.
    - Maksimal 5 poin/baris per jawaban kecuali diminta lebih detail.

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
    Status              : {"Memenuhi syarat SKS sidang" if bisa_sid else f"Belum memenuhi, kurang {kurang_sid} SKS"}

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


    === ATURAN SKPI (SURAT KETERANGAN PENDAMPING IJAZAH) ===
    SKPI wajib dipenuhi sebagai syarat kelulusan. Syarat-syaratnya:

    1. MINIMAL 5 SERTIFIKAT KEGIATAN
    Sertifikat dapat berasal dari: {', '.join(ATURAN_SKPI['syarat'][0]['kategori'])}.

    2. LOLOS PROGRAM KREATIVITAS MAHASISWA (PKM) TINGKAT UNIVERSITAS
    Minimal 1 kali lolos seleksi PKM di tingkat UPNVJ.
    Jenis PKM: {', '.join(ATURAN_SKPI['syarat'][1]['kategori'])}.

    3. SERTIFIKAT KEAHLIAN / PROFESI
    Minimal 1 sertifikat dari lembaga yang diakui UPNVJ:
    {', '.join(ATURAN_SKPI['syarat'][2]['lembaga_diakui'])}.

    4. SERTIFIKAT TOEFL / ELPT — SKOR MINIMAL {ATURAN_SKPI['syarat'][3]['skor_minimal']}
    Jenis tes yang diakui: {', '.join(ATURAN_SKPI['syarat'][3]['jenis_tes'])}.

    Gunakan semua data di atas untuk menjawab pertanyaan mahasiswa secara akurat.
    """
    return prompt


# Informasi tambahan dari admin (menambah pengetahuan chatbot)
def get_pengetahuan_tambahan() -> str:
    """Ambil informasi aktif dari admin dan append ke system prompt"""
    try:
        from src.models import InformasiChatbot
        aktif = InformasiChatbot.query\
            .filter_by(is_active=True)\
            .order_by(InformasiChatbot.id)\
            .all()
        if not aktif:
            return ""
        sections = [f"=== {p.judul.upper()} ===\n{p.konten}" for p in aktif]
        return "\n\n" + "\n\n".join(sections)
    except Exception:
        return ""


# Chat dengan deepseek
def chat(pesan: str, history: list, system_prompt: str, max_tokens: int = 1024) -> str:
    messages = [{"role": "system", "content": system_prompt}]
    messages += history
    messages.append({"role": "user", "content": pesan})

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.7,
            timeout=60,   # maksimal 60 detik tunggu DeepSeek
        )
        return response.choices[0].message.content

    except Exception as e:
        err_str = str(e).lower()
        if "timeout" in err_str or "timed out" in err_str:
            raise TimeoutError("DeepSeek API tidak merespons dalam 60 detik. Coba lagi.")
        if "connection" in err_str or "network" in err_str:
            raise ConnectionError("Gagal terhubung ke DeepSeek API. Periksa koneksi internet server.")
        raise RuntimeError(f"DeepSeek API error: {str(e)}")