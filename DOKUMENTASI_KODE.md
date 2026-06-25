# Dokumentasi Kode — FIKA: Asisten Konseling Akademik & Karier Mahasiswa FIK
> UPN "Veteran" Jakarta — Fakultas Ilmu Komputer
> Dibuat untuk keperluan Sidang Skripsi

---

## Gambaran Umum Sistem

FIKA adalah aplikasi chatbot konseling akademik untuk mahasiswa FIK UPNVJ. Sistem ini membantu mahasiswa memahami progress studi mereka dengan cara:
1. Mahasiswa mengunggah file **KHS (Kartu Hasil Studi)** dalam format PDF
2. Sistem membaca dan mengekstrak data dari PDF tersebut secara otomatis
3. Data KHS dibandingkan dengan **kurikulum resmi** program studi
4. Hasil analisis dijadikan **konteks** untuk chatbot berbasis AI (DeepSeek)
5. Mahasiswa dapat bertanya bebas tentang status akademiknya

**Stack Teknologi:**
- Backend: Python + Flask
- Frontend: React + TypeScript + Tailwind CSS
- Database: PostgreSQL
- AI: DeepSeek Chat API
- OCR PDF: pdfplumber

---

## Arsitektur Backend

```
backend/
├── app.py                          ← Entry point Flask
└── src/
    ├── models.py                   ← Tabel database (SQLAlchemy)
    ├── chatbot.py                  ← [INTI] Orkestrasi AI + System Prompt
    ├── ocr/
    │   └── khs_extractor.py        ← [INTI] Ekstraksi data dari PDF KHS
    ├── analysis/
    │   └── progress_analyzer.py    ← [INTI] Analisis progress studi mahasiswa
    ├── curriculum/
    │   └── curriculum_loader.py    ← Memuat data kurikulum dari DB/XLSX
    ├── rules/
    │   └── academic_rules.py       ← Konstanta aturan akademik
    └── api/
        ├── auth/routes.py          ← Endpoint autentikasi
        ├── chatbot/routes.py       ← Endpoint upload KHS & chat
        └── admin/routes.py         ← Endpoint manajemen admin
```

---

# BAGIAN 1 — KODE UTAMA (PENJELASAN DETAIL)

---

## 1.1 `khs_extractor.py` — Ekstraksi Data PDF KHS

**Lokasi:** [backend/src/ocr/khs_extractor.py](backend/src/ocr/khs_extractor.py)

**Tujuan:** Membaca file PDF KHS yang diunggah mahasiswa, mengekstrak teks dari halaman PDF, lalu mem-parsing teks tersebut menjadi data terstruktur (nama, NIM, IPK, daftar mata kuliah, dll).

### Struktur Data Output

```python
@dataclass
class MataKuliah:
    nama: str          # Nama mata kuliah
    nilai: Optional[str]  # Grade huruf: A, B+, C, dst
    HM: Optional[float]   # Grade angka: 4.0, 3.5, dst
    SKS: int           # Jumlah SKS mata kuliah tersebut
    M: Optional[float] # Mutu (HM × SKS)

@dataclass
class KHSData:
    nama_mahasiswa: str
    nim: str
    program_studi: str    # Misal: "S1 Informatika"
    ipk: float
    ips: float
    sks_kumulatif: int    # Total SKS yang sudah ditempuh
    sks_semester_lalu: int
    batas_ambil_sks: int
    matakuliah: list      # List of MataKuliah
    source_file: str
```

---

### Fungsi `normalize_prodi(raw)`
**Baris 42–47**

```python
PRODI_ALIASES = {
    "sistem informasi d-iii": "D3 Sistem Informasi",
    "sistem informasi s.1":   "S1 Sistem Informasi",
    "sains data s.1":         "S1 Sains Data",
    "informatika s.1":        "S1 Informatika",
}

def normalize_prodi(raw: str) -> str:
    key = raw.strip().lower()
    for alias, canonical in PRODI_ALIASES.items():
        if alias in key:
            return canonical
    return raw.strip().title()
```

**Cara kerja:**
- PDF KHS mencetak nama prodi dalam format bervariasi, misal `"Informatika S.1"` atau `"INFORMATIKA S.1"`
- Fungsi ini mengubahnya menjadi format standar `"S1 Informatika"` agar cocok dengan kunci di database dan aturan prodi
- Pertama-tama string diubah ke huruf kecil (`.lower()`), lalu dicari apakah mengandung salah satu alias yang sudah didefinisikan
- Jika tidak ada yang cocok, fungsi mengembalikan string aslinya dengan format judul (`.title()`)

---

### Fungsi `extract_header_info(text)`
**Baris 65–100**

```python
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
        info["ipk"]           = parse_float(m.group(2))

    m = re.search(
        r"Sks Semester Lalu\s*[:\-]\s*(\d+)\s*[,.]?\s*IPS[.\s]*(\d+[.,]\d+)",
        text, re.IGNORECASE
    )
    if m:
        info["sks_semester_lalu"] = int(m.group(1))
        info["ips"]               = parse_float(m.group(2))

    return info
```

**Cara kerja:**
- Fungsi ini menggunakan **Regular Expression (Regex)** untuk mencari pola teks tertentu di dalam teks penuh PDF
- Setiap field dicari dengan pola regex yang mentoleransi variasi format, misalnya `"Program Studi:"` atau `"Program Studi -"`
- `re.IGNORECASE` memastikan pencarian tidak terpengaruh huruf kapital/kecil
- `m.group(1)` mengambil bagian yang "ditangkap" (captured group) dari pola regex, yaitu nilai setelah tanda titik dua
- Regex paling kompleks adalah untuk IPK: `r"Prestasi Kumulatif\s*[:\-]\s*(\d+)\s*[,.]?\s*IPK[.\s]*(\d+[.,]\d+)"` yang menangkap sekaligus SKS kumulatif dan nilai IPK dari satu baris teks

---

### Regex Pattern Mata Kuliah `MK_PATTERN`
**Baris 112–121**

```python
MK_PATTERN = re.compile(
    r"^\s*(\d{1,3})"          # Nomor urut (1-3 digit)
    r"(?:\s+\[[\s]*\])?"      # Opsional: kotak centang [ ]
    r"\s+(.+?)"               # Nama mata kuliah (lazy match)
    r"(?:\s+(A[+-]?|B[+-]?|C[+-]?|D|E))?"  # Opsional: grade huruf
    r"\s+(\d+[.,]\d{2})"     # Grade angka (HM), misal 3.75
    r"\s+(\d{1,2})"           # SKS (1-2 digit)
    r"\s+(\d+[.,]\d{2})"     # Mutu (M), misal 11.25
    r"(?:\s+\*)?\s*$"         # Opsional: tanda bintang (*)
)
```

**Cara kerja:**
- Satu baris teks dari PDF KHS untuk satu mata kuliah memiliki format: `1  Pemrograman Dasar  A  4.00  3  12.00`
- Pola regex ini mengenali format tersebut dan menangkap setiap kolom sebagai captured group
- `(.+?)` menggunakan **lazy matching** agar nama matkul tidak "memakan" kolom berikutnya
- Pola grade huruf `(A[+-]?|B[+-]?|C[+-]?|D|E)` dibuat opsional karena beberapa baris mungkin tidak menampilkan grade huruf
- Tanda `(?:...)` adalah **non-capturing group** yang hanya untuk pengelompokan, tidak ditangkap sebagai output

---

### Fungsi `parse_single_line(line)`
**Baris 124–151**

```python
def parse_single_line(line: str) -> Optional[MataKuliah]:
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

    # Filter: lewati mata kuliah yang belum pernah diambil (HM = 0)
    if not grade_a or grade_a == 0.0:
        return None

    return MataKuliah(
        nama=nama,
        nilai=grade_h,
        HM=grade_a,
        SKS=sks,
        M=mutu if mutu and mutu > 0 else None,
    )
```

**Cara kerja:**
- Mengaplikasikan `MK_PATTERN` pada satu baris teks
- Baris yang tidak cocok dengan pola (misalnya judul tabel atau baris kosong) dikembalikan sebagai `None`
- `re.sub(r"\s*\(.*?\)\s*$", "", nama)` menghapus keterangan peminatan yang muncul di dalam kurung, misal `"Keamanan Siber (CE.1)"` menjadi `"Keamanan Siber"`
- **Filter penting:** Jika `grade_a == 0.0`, berarti mata kuliah ini terdaftar tapi belum pernah diambil mahasiswa — dilewati karena tidak relevan untuk analisis progress

---

### Fungsi `extract_lines_from_page(page)`
**Baris 155–163**

```python
def extract_lines_from_page(page) -> list:
    width  = page.width
    height = page.height

    left_text  = page.crop((0,            0, width * 0.50, height)).extract_text() or ""
    right_text = page.crop((width * 0.50, 0, width,        height)).extract_text() or ""

    return left_text.splitlines() + right_text.splitlines()
```

**Cara kerja:**
- KHS UPNVJ memiliki format **dua kolom** — semester genap di kiri, ganjil di kanan (atau sebaliknya)
- `pdfplumber` mendukung operasi `crop()` yang memotong area halaman berdasarkan koordinat
- Fungsi ini memotong halaman menjadi dua bagian sama rata (50% kiri, 50% kanan), mengekstrak teks masing-masing, lalu menggabungkan hasilnya baris per baris
- Ini memastikan semua mata kuliah dari kedua kolom terbaca dengan urutan yang benar

---

### Fungsi Utama `extract_khs_from_pdf(pdf_path)`
**Baris 167–207**

```python
def extract_khs_from_pdf(pdf_path) -> KHSData:
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"File tidak ditemukan: {pdf_path}")

    all_lines = []
    full_text = ""

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            full_text += "\n" + (page.extract_text() or "")  # untuk header
            all_lines.extend(extract_lines_from_page(page))  # untuk matkul

    header = extract_header_info(full_text)

    khs = KHSData(
        nama_mahasiswa = header.get("nama_mahasiswa", "UNKNOWN"),
        nim            = header.get("nim", "UNKNOWN"),
        program_studi  = header.get("program_studi", "UNKNOWN"),
        ipk            = header.get("ipk", 0.0),
        ips            = header.get("ips", 0.0),
        sks_kumulatif  = header.get("sks_kumulatif", 0),
        ...
    )

    seen = set()  # deduplikasi berdasarkan nama matakuliah

    for line in all_lines:
        if detect_semester_label(line):
            continue  # lewati baris "SEMESTER I", "SEMESTER II", dst

        mk = parse_single_line(line)
        if mk:
            key = mk.nama.lower()
            if key not in seen:
                seen.add(key)
                khs.matakuliah.append(mk)

    return khs
```

**Cara kerja (alur lengkap):**
1. **Buka PDF** menggunakan `pdfplumber.open()`
2. **Kumpulkan semua teks** — `full_text` untuk data header, `all_lines` untuk baris mata kuliah
3. **Ekstrak header** — nama, NIM, prodi, IPK, IPS, SKS kumulatif dari `full_text`
4. **Iterasi setiap baris** — lewati label semester, parse setiap baris sebagai mata kuliah
5. **Deduplikasi** — `seen` set mencegah mata kuliah yang sama tercatat dua kali (bisa terjadi jika PDF memiliki halaman berulang)
6. **Return** objek `KHSData` yang sudah lengkap

---

## 1.2 `progress_analyzer.py` — Analisis Progress Studi

**Lokasi:** [backend/src/analysis/progress_analyzer.py](backend/src/analysis/progress_analyzer.py)

**Tujuan:** Membandingkan daftar mata kuliah yang sudah diambil mahasiswa (dari KHS) dengan kurikulum resmi program studi, lalu menghasilkan laporan lengkap tentang progress studi, status peminatan, dan kelayakan sidang.

### Struktur Data Output

```python
@dataclass
class HasilAnalisis:
    # Info mahasiswa
    nama_mahasiswa: str
    nim: str
    program_studi: str
    ipk: float
    ips: float

    # SKS
    sks_kumulatif: int          # SKS resmi dari KHS
    total_sks_kurikulum: int    # Total SKS kurikulum (misal 144)
    sks_wajib_lulus: int        # SKS minimum kelulusan
    sks_sudah_tempuh: int       # SKS yang sudah ditempuh
    sks_belum_tempuh: int       # Sisa SKS

    # Statistik mata kuliah
    jumlah_mk_lulus: int
    jumlah_mk_belum: int

    # Aturan prodi
    total_semester: int
    syarat_sidang_sks: int      # SKS minimum untuk boleh sidang
    bisa_sidang: bool           # True jika SKS sudah mencukupi

    # Peminatan
    peminatan_info: list        # Detail per jalur peminatan
    peminatan_konsisten: bool   # True jika hanya ambil 1 jalur
    peminatan_pesan: str        # Pesan deskriptif

    # Detail matkul
    mk_sudah_lulus: list        # List MKSudahLulus
    mk_belum_diambil: list      # List MKBelumDiambil
```

---

### Fungsi `normalize_nama(nama)`
**Baris 80–84**

```python
def normalize_nama(nama: str) -> str:
    nama = nama.lower().strip()
    nama = re.sub(r"[/\(\)\[\]\*\+]", " ", nama)
    nama = re.sub(r"\s+", " ", nama)
    return nama.strip()
```

**Cara kerja:**
- Sebelum membandingkan nama matkul dari KHS dengan kurikulum, keduanya harus "dinormalisasi" terlebih dahulu
- Mengubah ke huruf kecil (menangani `"PEMROGRAMAN DASAR"` vs `"Pemrograman Dasar"`)
- Mengganti karakter khusus `/`, `(`, `)`, `[`, `]`, `*`, `+` dengan spasi
- Menghilangkan spasi ganda menjadi spasi tunggal
- Contoh: `"Rekayasa Perangkat Lunak (RPL)"` → `"rekayasa perangkat lunak rpl"`

---

### Fungsi `is_match(nama_khs, nama_kurikulum)`
**Baris 92–118 — Fungsi Paling Kritis**

Ini adalah jantung dari sistem analisis. Fungsi ini menentukan apakah sebuah mata kuliah dari KHS mahasiswa cocok (sama) dengan mata kuliah yang ada di kurikulum.

```python
def is_match(nama_khs: str, nama_kurikulum: str) -> bool:
    a = normalize_nama(nama_khs)
    b = normalize_nama(nama_kurikulum)

    # Strategi 1: Kecocokan Persis
    if a == b:
        return True

    # Strategi 2: Substring (salah satu mengandung yang lain)
    if len(a) > 5 and len(b) > 5:
        if a in b or b in a:
            return True
        # Strategi 2b: Tanpa Spasi (menangani word-break PDF)
        if _tanpa_spasi(a) == _tanpa_spasi(b):
            return True

    # Strategi 3: Token Subset (kata-kata yang lebih pendek ada di yang lebih panjang)
    tokens_a = set(a.split())
    tokens_b = set(b.split())
    shorter = tokens_a if len(tokens_a) <= len(tokens_b) else tokens_b
    longer  = tokens_b if len(tokens_a) <= len(tokens_b) else tokens_a
    if len(shorter) >= 2 and shorter.issubset(longer):
        return True

    # Strategi 4: Fuzzy Matching (menangani typo/perbedaan ejaan kecil)
    if len(a) > 8 and len(b) > 8:
        ratio = SequenceMatcher(None, a, b).ratio()
        if ratio >= 0.88:
            return True

    return False
```

**Mengapa perlu 4 strategi berbeda?**

PDF KHS sering menghasilkan teks yang tidak sempurna karena:
- Keterbatasan font PDF (nama matkul terpotong, ada spasi ekstra)
- Perbedaan ejaan antara KHS lama dan kurikulum baru
- Singkatan atau variasi penulisan

Berikut penjelasan masing-masing strategi:

| Strategi | Kasus yang Ditangani | Contoh |
|---|---|---|
| **1. Kecocokan Persis** | Nama benar-benar sama setelah normalisasi | `"pemrograman dasar"` == `"pemrograman dasar"` |
| **2. Substring** | Satu nama mengandung nama lain secara penuh | `"basis data"` ada di `"basis data lanjut"` |
| **2b. Tanpa Spasi** | PDF memotong nama jadi satu kata | `"technopreneurship"` == `"techno preneurship"` |
| **3. Token Subset** | Nama yang lebih pendek semua katanya ada di yang lebih panjang | `{"sistem", "basis"}` ⊆ `{"sistem", "basis", "data"}` |
| **4. Fuzzy Match** | Perbedaan ejaan kecil, min 88% mirip | `"jaringan komputer"` ≈ `"jaringan komputasi"` |

**Kenapa threshold 88% di fuzzy matching?**
- `SequenceMatcher` dari Python menghitung rasio kesamaan karakter (0.0 = berbeda total, 1.0 = identik)
- 88% dipilih sebagai keseimbangan antara tidak terlalu ketat (melewatkan kecocokan yang benar) dan tidak terlalu longgar (menganggap dua matkul berbeda sebagai sama)

---

### Fungsi `analisis_peminatan(mk_lulus, prodi)`
**Baris 122–175**

```python
def analisis_peminatan(mk_lulus: list, prodi: str) -> tuple:
    aturan = PEMINATAN_PRODI.get(prodi)
    if not aturan or not aturan["harus_konsisten"]:
        return [], True, "Tidak ada aturan peminatan khusus untuk prodi ini."

    jalur_map = aturan["jalur"]   # Misal: {"CE": "Cybersecurity", "NE": "Network", ...}
    min_mk    = aturan["min_mk_per_jalur"]  # Minimal 3 MK per jalur

    # Hitung berapa MK peminatan yang diambil per jalur
    counter = {kode: 0 for kode in jalur_map}

    for mk in mk_lulus:
        ket = (mk.get("keterangan") or "").upper()
        for kode in jalur_map:
            if kode in ket:   # Misal: "Peminatan CE.1" mengandung "CE"
                counter[kode] += 1
                break

    # Buat list InfoPeminatan untuk setiap jalur
    info_list = []
    for kode, nama in jalur_map.items():
        jumlah = counter[kode]
        info_list.append(InfoPeminatan(
            jalur_kode  = kode,
            jalur_nama  = nama,
            jumlah_mk   = jumlah,
            sudah_cukup = jumlah >= min_mk,
            min_required = min_mk,
        ))

    # Cek konsistensi: hanya boleh ambil dari 1 jalur
    jalur_diambil = [kode for kode, jml in counter.items() if jml > 0]
    konsisten = len(jalur_diambil) <= 1

    # Buat pesan deskriptif sesuai kondisi
    if not jalur_diambil:
        pesan = "Belum mengambil mata kuliah peminatan apapun."
    elif not konsisten:
        pesan = (f"Mengambil MK dari {len(jalur_diambil)} jalur peminatan berbeda "
                 f"({', '.join(jalur_diambil)}). Seharusnya hanya 1 jalur.")
    else:
        kode_aktif = jalur_diambil[0]
        jml_aktif  = counter[kode_aktif]
        nama_aktif = jalur_map[kode_aktif]
        if jml_aktif >= min_mk:
            pesan = (f"Peminatan {nama_aktif} ({kode_aktif}): "
                     f"{jml_aktif} MK sudah diambil (syarat minimal {min_mk} MK).")
        else:
            kurang = min_mk - jml_aktif
            pesan  = (f"Peminatan {nama_aktif} ({kode_aktif}): "
                      f"{jml_aktif}/{min_mk} MK. Masih kurang {kurang} MK lagi.")

    return info_list, konsisten, pesan
```

**Cara kerja:**
1. Ambil aturan peminatan dari `PEMINATAN_PRODI` berdasarkan prodi mahasiswa
2. Untuk D3 Sistem Informasi: tidak ada peminatan → langsung return "tidak ada aturan"
3. Inisialisasi `counter` untuk menghitung berapa MK peminatan yang diambil per jalur
4. Loop setiap mata kuliah yang lulus, cek kolom `keterangan` apakah mengandung kode jalur (CE, NE, SE, AU, AD, ES, DE, DA)
5. Hitung jalur mana yang sudah diambil — jika lebih dari 1 jalur, berarti **tidak konsisten**
6. Return tiga nilai: list info per jalur, status konsistensi (bool), dan pesan deskriptif

---

### Fungsi Utama `analyze_progress(khs, kurikulum)`
**Baris 179–252 — Fungsi Inti Analisis**

```python
def analyze_progress(khs: KHSData, kurikulum: Kurikulum) -> HasilAnalisis:
    # 1. Ambil aturan prodi (SKS kelulusan, total semester, syarat sidang)
    aturan       = ATURAN_PRODI.get(khs.program_studi, {})
    sks_wajib    = aturan.get("sks_lulus", 144)
    total_sem    = aturan.get("total_semester", 8)
    syarat_sidang = aturan.get("syarat_sidang_sks", 138)

    mk_lulus = []
    mk_belum = []
    sks_tempuh = 0

    # 2. Buat dictionary dari KHS untuk pencarian cepat
    nama_lulus_khs = {normalize_nama(mk.nama): mk for mk in khs.matakuliah if mk.HM}

    # 3. Loop setiap MK di kurikulum, cari padanannya di KHS
    for mk_kur in kurikulum.matakuliah:
        nama_kur_norm = normalize_nama(mk_kur.nama)

        matched_mk = None
        for nama_khs_norm, mk_khs in nama_lulus_khs.items():
            if is_match(nama_khs_norm, nama_kur_norm):
                matched_mk = mk_khs
                break

        if matched_mk:
            # MK ini sudah pernah diambil & lulus
            mk_lulus.append(MKSudahLulus(
                nama              = mk_kur.nama,      # Nama resmi dari kurikulum
                kode              = mk_kur.kode,
                semester_kurikulum = mk_kur.semester,
                nilai             = matched_mk.nilai,  # Grade dari KHS mahasiswa
                HM                = matched_mk.HM,
                SKS               = mk_kur.sks,
                M                 = matched_mk.M,
                keterangan        = mk_kur.keterangan,
            ))
            sks_tempuh += mk_kur.sks
        else:
            # MK ini belum diambil
            mk_belum.append(MKBelumDiambil(
                nama              = mk_kur.nama,
                kode              = mk_kur.kode,
                semester_kurikulum = mk_kur.semester,
                sks               = mk_kur.sks,
                keterangan        = mk_kur.keterangan,
            ))

    # 4. Gunakan SKS kumulatif resmi dari KHS (lebih akurat dari penghitungan manual)
    sks_resmi  = khs.sks_kumulatif if khs.sks_kumulatif else sks_tempuh
    sks_belum  = max(sks_wajib - sks_resmi, 0)
    bisa_sidang = sks_resmi >= syarat_sidang

    # 5. Analisis peminatan
    mk_lulus_dict = [asdict(m) for m in mk_lulus]
    peminatan_info, peminatan_konsisten, peminatan_pesan = analisis_peminatan(
        mk_lulus_dict, khs.program_studi
    )

    # 6. Kembalikan hasil lengkap
    return HasilAnalisis(
        nama_mahasiswa    = khs.nama_mahasiswa,
        nim               = khs.nim,
        ...
        bisa_sidang       = bisa_sidang,
        peminatan_info    = [asdict(p) for p in peminatan_info],
        ...
        mk_sudah_lulus    = mk_lulus_dict,
        mk_belum_diambil  = [asdict(m) for m in mk_belum],
    )
```

**Alur kerja lengkap:**
1. **Load aturan prodi** — SKS kelulusan, total semester, batas SKS sidang dari `ATURAN_PRODI`
2. **Buat index KHS** — dict `{nama_normalisasi: objek_matkul}` dari semua matkul yang sudah ditempuh mahasiswa, untuk pencarian O(n) yang efisien
3. **Pencocokan kurikulum vs KHS** — untuk setiap mata kuliah dalam kurikulum resmi, cari apakah ada padanannya di KHS mahasiswa menggunakan fungsi `is_match()`. Ini adalah loop O(n×m) dimana n = jumlah MK kurikulum, m = jumlah MK mahasiswa
4. **Hitung SKS** — gunakan `sks_kumulatif` dari KHS sebagai nilai resmi (sudah dihitung sistem akademik); jika tidak ada, gunakan hitungan manual
5. **Cek kelayakan sidang** — `bisa_sidang = sks_resmi >= syarat_sidang`
6. **Analisis peminatan** — panggil `analisis_peminatan()` dan gabungkan hasilnya
7. **Return** objek `HasilAnalisis` dengan semua data lengkap

**Keputusan Desain Penting:**
- Nama yang dipakai di `mk_sudah_lulus` adalah nama dari **kurikulum** (bukan dari KHS). Ini memastikan konsistensi terminologi dalam sistem
- `asdict()` mengubah dataclass menjadi dictionary biasa agar bisa disimpan ke JSON di database

---

## 1.3 `chatbot.py` — Orkestrasi AI & System Prompt

**Lokasi:** [backend/src/chatbot.py](backend/src/chatbot.py)

**Tujuan:** Mengorkestrasikan seluruh alur: memproses PDF KHS, membangun konteks untuk AI, dan mengirim/menerima pesan dari DeepSeek API.

---

### Setup DeepSeek Client
**Baris 15–18**

```python
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)
```

**Cara kerja:**
- DeepSeek API **kompatibel dengan format OpenAI API**, sehingga library `openai` bisa digunakan langsung
- Hanya `base_url` yang diganti menunjuk ke server DeepSeek
- `api_key` dibaca dari environment variable (file `.env`) demi keamanan

---

### Lazy Loading Kurikulum
**Baris 24–39**

```python
_SEMUA_KURIKULUM = None  # Cache global

def get_semua_kurikulum() -> dict:
    """Lazy load kurikulum dari DB. Di-cache setelah load pertama."""
    global _SEMUA_KURIKULUM
    if _SEMUA_KURIKULUM is None:
        _SEMUA_KURIKULUM = load_all_kurikulum_from_db()
    return _SEMUA_KURIKULUM

def reload_kurikulum():
    """Paksa reload kurikulum dari DB (dipanggil setelah admin ubah kurikulum)."""
    global _SEMUA_KURIKULUM
    _SEMUA_KURIKULUM = load_all_kurikulum_from_db()
    return _SEMUA_KURIKULUM
```

**Cara kerja:**
- **Lazy loading**: kurikulum tidak dimuat saat aplikasi pertama start, melainkan saat pertama kali dibutuhkan. Ini mencegah crash jika database belum siap saat startup
- **Caching**: setelah di-load pertama kali, disimpan di variabel global `_SEMUA_KURIKULUM`. Request berikutnya langsung pakai cache tanpa query ke database
- **Cache invalidation**: saat admin mengubah data kurikulum lewat halaman admin, route admin memanggil `reload_kurikulum()` untuk memaksa reload dari database

---

### Fungsi `proses_khs(pdf_path)`
**Baris 43–53**

```python
def proses_khs(pdf_path: str) -> dict:
    khs      = extract_khs_from_pdf(pdf_path)
    kurikulum = get_semua_kurikulum().get(khs.program_studi)
    if not kurikulum:
        raise ValueError(
            f"Kurikulum untuk prodi '{khs.program_studi}' tidak ditemukan.\n"
            f"Prodi tersedia: {', '.join(get_semua_kurikulum().keys())}"
        )
    hasil = analyze_progress(khs, kurikulum)
    return asdict(hasil)
```

**Cara kerja:**
- Fungsi orchestrator yang menggabungkan tiga modul utama menjadi satu pipeline:
  1. `extract_khs_from_pdf()` → mengekstrak data dari PDF KHS
  2. `get_semua_kurikulum().get(prodi)` → mengambil kurikulum yang sesuai prodi mahasiswa
  3. `analyze_progress()` → menganalisis progress berdasarkan KHS vs kurikulum
- `asdict()` mengubah dataclass menjadi dictionary agar bisa di-serialize ke JSON dan disimpan ke database

---

### Fungsi `build_system_prompt(hasil)`
**Baris 57–155 — Fungsi Terpanjang dan Sangat Penting**

```python
def build_system_prompt(hasil: dict) -> str:
    persen    = (hasil['sks_sudah_tempuh'] / hasil['total_sks_kurikulum'] * 100)
    bisa_sid  = hasil['bisa_sidang']
    kurang_sid = hasil['syarat_sidang_sks'] - hasil['sks_sudah_tempuh']

    # Format daftar MK lulus menjadi teks
    mk_lulus_text = "\n".join([
        f"  - {mk['nama']} | Nilai: {mk['nilai'] or '-'} | HM: {mk['HM']} "
        f"| {mk['SKS']} SKS | Sem.{mk['semester_kurikulum']} | [{mk.get('keterangan','-')}]"
        for mk in hasil['mk_sudah_lulus']
    ])

    # Format daftar MK belum diambil menjadi teks
    mk_belum_text = "\n".join([...])

    # Format info peminatan menjadi teks
    peminatan_text = "\n".join([
        f"  - {p['jalur_kode']} ({p['jalur_nama']}): "
        f"{p['jumlah_mk']}/{p['min_required']} MK "
        f"{'✅' if p['sudah_cukup'] else '❌'}"
        for p in hasil.get('peminatan_info', [])
    ])

    prompt = f"""Kamu adalah asisten akademik chatbot bernama FIKA...
    
    === DATA MAHASISWA ===
    Nama  : {hasil['nama_mahasiswa']}
    NIM   : {hasil['nim']}
    ...

    === PROGRESS SKS ===
    SKS Sudah Tempuh : {hasil['sks_sudah_tempuh']} SKS
    Progress         : {persen:.1f}%
    ...

    === DAFTAR MK SUDAH LULUS ===
    {mk_lulus_text}

    === DAFTAR MK BELUM DIAMBIL ===
    {mk_belum_text}

    === ATURAN SKPI ===
    ...
    """
    return prompt
```

**Cara kerja:**
- Fungsi ini membangun **system prompt** — instruksi awal yang diberikan ke model AI sebelum percakapan dimulai
- System prompt berisi:
  - **Identitas chatbot**: nama FIKA, fakultas, instruksi cara menjawab (ringkas, Bahasa Indonesia, gunakan tabel Markdown)
  - **Data lengkap mahasiswa**: dari hasil analisis KHS
  - **Progress SKS**: sudah tempuh, belum tempuh, persentase
  - **Status sidang**: apakah sudah memenuhi syarat atau belum
  - **Daftar semua mata kuliah**: yang lulus (dengan nilai) dan yang belum diambil
  - **Analisis peminatan**: status per jalur
  - **Aturan SKPI**: syarat non-akademik untuk kelulusan

- **Pendekatan ini disebut "Prompt Engineering"**: alih-alih melatih model AI baru, kita memasukkan semua data relevan ke dalam instruksi sistem agar AI bisa menjawab berdasarkan data spesifik mahasiswa
- Panjang system prompt bisa mencapai ribuan karakter, namun ini yang memungkinkan AI menjawab pertanyaan spesifik seperti "MK apa yang belum saya ambil di semester 5?"

---

### Fungsi `get_pengetahuan_tambahan()`
**Baris 159–172**

```python
def get_pengetahuan_tambahan() -> str:
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
```

**Cara kerja:**
- Admin dapat menambahkan informasi tambahan melalui halaman admin (contoh: pengumuman pendaftaran PKM, jadwal perwalian, info beasiswa)
- Semua informasi yang `is_active=True` di-query dari database dan digabungkan menjadi teks
- Teks ini akan di-append ke system prompt agar chatbot juga mengetahui informasi tambahan tersebut
- Menggunakan `try/except` karena dipanggil saat startup, sebelum DB pasti siap

---

### Fungsi `chat(pesan, history, system_prompt, max_tokens)`
**Baris 176–197**

```python
def chat(pesan: str, history: list, system_prompt: str, max_tokens: int = 1024) -> str:
    # Susun messages: system → history → pesan baru
    messages = [{"role": "system", "content": system_prompt}]
    messages += history
    messages.append({"role": "user", "content": pesan})

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.7,
            timeout=60,
        )
        return response.choices[0].message.content

    except Exception as e:
        err_str = str(e).lower()
        if "timeout" in err_str or "timed out" in err_str:
            raise TimeoutError("DeepSeek API tidak merespons dalam 60 detik.")
        if "connection" in err_str or "network" in err_str:
            raise ConnectionError("Gagal terhubung ke DeepSeek API.")
        raise RuntimeError(f"DeepSeek API error: {str(e)}")
```

**Cara kerja:**
- Menyusun array `messages` dalam format yang diperlukan DeepSeek/OpenAI API:
  1. **System message** — instruksi dan konteks data mahasiswa (`system_prompt`)
  2. **History messages** — maksimal 20 pesan terakhir dari sesi chat yang sama (memungkinkan AI mengingat konteks percakapan)
  3. **Pesan baru** dari mahasiswa
- Parameter penting:
  - `temperature=0.7` — mengatur kreativitas jawaban (0 = deterministik, 1 = sangat kreatif). 0.7 dipilih agar jawaban natural tapi tetap akurat
  - `max_tokens=1024` — batas panjang jawaban
  - `timeout=60` — batas waktu tunggu 60 detik
- Error handling membedakan tipe error agar frontend bisa menampilkan pesan yang tepat

---

# BAGIAN 2 — FILE PENDUKUNG (PENJELASAN FUNGSI)

---

## 2.1 `academic_rules.py` — Konstanta Aturan Akademik

**Lokasi:** [backend/src/rules/academic_rules.py](backend/src/rules/academic_rules.py)

File ini berisi **4 konstanta dictionary** yang mendefinisikan aturan akademik FIK UPNVJ secara hardcode:

| Konstanta | Isi |
|---|---|
| `ATURAN_PRODI` | SKS kelulusan, total semester, beban SKS per semester, syarat SKS sidang untuk setiap prodi (D3 SI, S1 SI, S1 SD, S1 Informatika) |
| `PEMINATAN_PRODI` | Jalur-jalur peminatan yang tersedia per prodi, kode jalur, nama jalur, jumlah MK minimum per jalur, dan apakah mahasiswa harus konsisten di satu jalur |
| `KETERANGAN_MK` | Deskripsi lengkap setiap kategori mata kuliah: MKWU, MKPS, MBKM, PLPS, Peminatan, Pilihan |
| `ATURAN_SKPI` | Semua syarat SKPI: 5 sertifikat kegiatan, 1 PKM, 1 sertifikat profesi, TOEFL/ELPT min 450 |

File ini berfungsi sebagai **"single source of truth"** untuk aturan akademik yang digunakan oleh `progress_analyzer.py` dan `chatbot.py`.

---

## 2.2 `curriculum_loader.py` — Pemuat Kurikulum

**Lokasi:** [backend/src/curriculum/curriculum_loader.py](backend/src/curriculum/curriculum_loader.py)

File ini bertanggung jawab memuat data kurikulum dari dua sumber berbeda:

| Fungsi | Sumber | Digunakan oleh |
|---|---|---|
| `load_all_kurikulum_from_db()` | PostgreSQL (production) | `chatbot.py` untuk analisis sehari-hari |
| `load_kurikulum_from_db(prodi)` | PostgreSQL (production) | Jika hanya butuh 1 prodi |
| `load_kurikulum(xlsx_path)` | File XLSX | `seed_kurikulum.py` saat setup awal |
| `load_all_kurikulum(dir)` | Folder berisi XLSX | `seed_kurikulum.py` saat setup awal |

Output semua fungsi adalah objek `Kurikulum` yang berisi list `MataKuliahKurikulum`. Di production, data selalu dibaca dari database agar admin bisa mengubah kurikulum tanpa perlu deploy ulang.

---

## 2.3 `models.py` — Skema Database

**Lokasi:** [backend/src/models.py](backend/src/models.py)

Mendefinisikan 6 tabel database menggunakan SQLAlchemy ORM:

| Tabel | Kelas | Isi |
|---|---|---|
| `informasi_chatbot` | `InformasiChatbot` | Pengetahuan tambahan yang dikelola admin, di-inject ke system prompt |
| `kurikulum_prodi` | `KurikulumProdi` | Master data program studi: nama, total semester, SKS kelulusan, aturan peminatan (JSON) |
| `mata_kuliah_kurikulum` | `MataKuliahKurikulum` | Daftar mata kuliah per prodi: kode, nama, SKS, semester, keterangan, prasyarat |
| `khs_uploads` | `KHSUpload` | Riwayat KHS yang diupload: NIM mahasiswa, waktu upload, hasil analisis (JSON), cache rekomendasi |
| `chat_sessions` | `ChatSession` | Sesi percakapan: ID (UUID), NIM, system prompt, judul, waktu aktif terakhir |
| `chat_messages` | `ChatMessage` | Pesan individual: session_id, role (user/assistant), isi, waktu |

Relasi antar tabel:
- `KurikulumProdi` → `MataKuliahKurikulum` (one-to-many, cascade delete)
- `KHSUpload` → `ChatSession` (one-to-many, cascade delete)
- `ChatSession` → `ChatMessage` (one-to-many, cascade delete)

---

## 2.4 `app.py` — Entry Point Flask

**Lokasi:** [backend/app.py](backend/app.py)

**Fungsi:** Menginisialisasi aplikasi Flask, mengonfigurasi database, mengaktifkan CORS, dan mendaftarkan semua Blueprint (grup route). Juga membuat semua tabel database saat startup pertama kali.

---

## 2.5 `auth/routes.py` — Autentikasi Pengguna

**Lokasi:** [backend/src/api/auth/routes.py](backend/src/api/auth/routes.py)

Menyediakan endpoint-endpoint untuk manajemen akun:
- `POST /api/register` — Daftarkan mahasiswa baru (NIM, nama, email, password)
- `POST /api/login` — Login, mengembalikan **JWT Token** yang berlaku 7 hari
- `POST /api/forgot-password` — Kirim link reset ke email (dibatasi 3 request/jam)
- `POST /api/reset-password` — Reset password menggunakan token dari email
- `GET /api/me` — Ambil data user yang sedang login
- `POST /api/logout` — Logout (token dihapus di sisi client)

Password disimpan dalam bentuk **hash** menggunakan Werkzeug. JWT token diverifikasi di setiap endpoint yang membutuhkan autentikasi.

---

## 2.6 `chatbot/routes.py` — Endpoint Chat & Upload KHS

**Lokasi:** [backend/src/api/chatbot/routes.py](backend/src/api/chatbot/routes.py)

Menyediakan endpoint-endpoint untuk fitur utama chatbot:

| Endpoint | Method | Fungsi |
|---|---|---|
| `/api/upload` | POST | Upload PDF KHS → ekstrak → analisis → buat sesi chat baru |
| `/api/chat` | POST | Kirim pesan ke AI, simpan percakapan ke DB |
| `/api/sessions` | GET | List semua sesi chat milik mahasiswa |
| `/api/sessions/<id>` | GET | Muat percakapan lengkap satu sesi |
| `/api/sessions/<id>` | DELETE | Hapus sesi chat |
| `/api/sessions/<id>/khs` | GET | Ambil data hasil analisis KHS sesi tersebut |
| `/api/sessions/<id>/rekomendasi` | GET | Generate rekomendasi MK & karier via AI (di-cache) |
| `/api/khs/latest` | GET | Ambil KHS upload terakhir mahasiswa |

Endpoint `/api/chat` mengambil 20 pesan terakhir dari sesi sebagai history agar AI memiliki konteks percakapan sebelumnya.

---

## 2.7 `admin/routes.py` — Manajemen Admin

**Lokasi:** [backend/src/api/admin/routes.py](backend/src/api/admin/routes.py)

Menyediakan endpoint CRUD untuk pengelolaan data oleh admin (membutuhkan role `admin`):

- **Kurikulum** — CRUD program studi, CRUD mata kuliah, import massal dari XLSX
- **Pengetahuan Chatbot** — CRUD informasi yang di-inject ke system prompt
- **Pengguna** — Lihat semua user, ubah role antara mahasiswa dan admin

Setiap perubahan data kurikulum memanggil `reload_kurikulum()` agar cache kurikulum di memori diperbarui.

---

# BAGIAN 3 — FRONTEND (PENJELASAN FUNGSI)

Frontend dibangun dengan **React + TypeScript + Vite + Tailwind CSS**.

| File | Fungsi |
|---|---|
| [frontend/src/App.tsx](frontend/src/App.tsx) | Routing utama: login, register, dashboard mahasiswa, halaman admin. Protected routes berdasarkan status login dan role |
| [frontend/src/pages/Dashboard/HomePage.tsx](frontend/src/pages/Dashboard/HomePage.tsx) | Dashboard utama mahasiswa: tampilan beranda dengan card fitur, tampilan chat, integrasi semua modal |
| [frontend/src/pages/LoginPage.tsx](frontend/src/pages/LoginPage.tsx) | Halaman login dengan form NIM + password, info fitur sistem, dan langkah penggunaan |
| [frontend/src/pages/Admin/AdminPage.tsx](frontend/src/pages/Admin/AdminPage.tsx) | Halaman manajemen admin: tab kurikulum, informasi chatbot, pengguna |
| [frontend/src/pages/Dashboard/Uploadkhsmodal.tsx](frontend/src/pages/Dashboard/Uploadkhsmodal.tsx) | Modal upload PDF KHS: drag-drop, progress upload, tampilkan hasil ekstraksi |
| [frontend/src/pages/Dashboard/RekomendasiModal.tsx](frontend/src/pages/Dashboard/RekomendasiModal.tsx) | Modal rekomendasi: tampilkan saran mata kuliah semester berikutnya dan saran karier dari AI |
| [frontend/src/pages/Dashboard/RiwayatModal.tsx](frontend/src/pages/Dashboard/RiwayatModal.tsx) | Modal riwayat chat: list semua sesi percakapan sebelumnya |
| [frontend/src/components/Chat/ChatBubble.tsx](frontend/src/components/Chat/ChatBubble.tsx) | Tampilan satu baris chat (user vs AI), mendukung render Markdown dan tabel |
| [frontend/src/components/Chat/ChatInput.tsx](frontend/src/components/Chat/ChatInput.tsx) | Input pesan: text field, tombol kirim, tombol upload KHS |
| [frontend/src/hooks/useChat.tsx](frontend/src/hooks/useChat.tsx) | Custom hook yang mengelola semua state chat: daftar pesan, loading, sesi aktif, pengiriman pesan, timeout 70 detik |
| [frontend/src/services/api.ts](frontend/src/services/api.ts) | Axios instance dengan interceptor otomatis menambahkan JWT token ke setiap request |
| [frontend/src/services/authServices.ts](frontend/src/services/authServices.ts) | Fungsi-fungsi autentikasi: login, register, logout, getMe. Token disimpan di localStorage |
| [frontend/src/services/adminServices.ts](frontend/src/services/adminServices.ts) | Fungsi-fungsi API untuk fitur admin: CRUD prodi, CRUD mata kuliah, CRUD pengetahuan, import XLSX |

---

# BAGIAN 4 — ALUR SISTEM LENGKAP

### Alur Upload KHS & Analisis Progress

```
Mahasiswa upload PDF KHS
        ↓
[Frontend] POST /api/upload (multipart/form-data)
        ↓
[chatbot/routes.py] Simpan file sementara
        ↓
[chatbot.py] proses_khs(pdf_path)
    ↓
    [khs_extractor.py] extract_khs_from_pdf()
    → Buka PDF dengan pdfplumber
    → Crop halaman kiri & kanan
    → Regex header (nama, NIM, prodi, IPK, IPS)
    → Regex setiap baris → parse MataKuliah
    → Deduplikasi
    → Return KHSData
    ↓
    [chatbot.py] get_semua_kurikulum().get(prodi)
    → Load dari cache / DB
    ↓
    [progress_analyzer.py] analyze_progress(khs, kurikulum)
    → Loop setiap MK kurikulum
    → is_match() dengan setiap MK di KHS
    → Klasifikasikan: lulus / belum
    → Hitung SKS, cek sidang
    → analisis_peminatan()
    → Return HasilAnalisis
        ↓
[chatbot/routes.py] Simpan ke KHSUpload (DB)
        ↓
[chatbot.py] build_system_prompt(hasil)
→ Format semua data ke teks panjang
→ Tambahkan aturan SKPI
→ Tambahkan pengetahuan admin
        ↓
[chatbot/routes.py] Buat ChatSession baru (DB)
        ↓
[Frontend] Tampilkan summary analisis ke mahasiswa
```

### Alur Chat dengan AI

```
Mahasiswa ketik pertanyaan
        ↓
[Frontend useChat hook] POST /api/chat
        ↓
[chatbot/routes.py]
→ Load 20 pesan terakhir dari DB (sebagai history)
→ Load system_prompt dari ChatSession
→ Append pengetahuan admin ke system_prompt
        ↓
[chatbot.py] chat(pesan, history, system_prompt)
→ Susun messages: [system] + [history] + [pesan_baru]
→ POST ke DeepSeek API
→ Timeout 60 detik
→ Return teks jawaban
        ↓
[chatbot/routes.py]
→ Simpan pesan user ke DB
→ Simpan jawaban AI ke DB
→ Return jawaban ke frontend
        ↓
[Frontend] Render jawaban dengan Markdown
```

---

# RINGKASAN

| Komponen | Teknologi | Peran |
|---|---|---|
| PDF Extraction | pdfplumber + Regex | Baca dan parse KHS dari format PDF yang tidak terstruktur |
| Fuzzy Matching | SequenceMatcher + Heuristic | Cocokkan nama MK dari KHS (bisa typo/format berbeda) ke kurikulum resmi |
| Progress Analysis | Python dataclass | Klasifikasi MK lulus/belum, hitung SKS, cek peminatan & sidang |
| AI Integration | DeepSeek API | Jawab pertanyaan mahasiswa berdasarkan konteks data spesifik mereka |
| Prompt Engineering | System Prompt injection | Masukkan semua data analisis ke instruksi AI agar bisa menjawab akurat |
| Database | PostgreSQL + SQLAlchemy | Simpan kurikulum, KHS upload, sesi & pesan chat |
| Web API | Flask + Blueprint | Expose fungsionalitas backend sebagai REST API |
| Frontend | React + TypeScript | Antarmuka pengguna yang responsif dengan render Markdown |
| Auth | JWT Token | Autentikasi stateless untuk REST API |
