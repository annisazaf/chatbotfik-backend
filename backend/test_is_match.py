import re
from difflib import SequenceMatcher


#Fungsi normalisasi

def normalize_nama(nama: str) -> str:
    nama = nama.lower().strip()
    nama = re.sub(r"[/\(\)\[\]\*\+]", " ", nama)
    nama = re.sub(r"\s+", " ", nama)
    return nama.strip()

def _tanpa_spasi(nama: str) -> str:
    return nama.replace(" ", "")


#Exact Match
def cara1_exact(nama_khs: str, nama_kurikulum: str) -> bool:
    a = normalize_nama(nama_khs)
    b = normalize_nama(nama_kurikulum)
    return a == b


#Substring
def cara2_substring(nama_khs: str, nama_kurikulum: str) -> bool:
    a = normalize_nama(nama_khs)
    b = normalize_nama(nama_kurikulum)
    if len(a) > 5 and len(b) > 5:
        return a in b or b in a
    return False


#Tanpa Spasi
def cara3_tanpa_spasi(nama_khs: str, nama_kurikulum: str) -> bool:
    a = normalize_nama(nama_khs)
    b = normalize_nama(nama_kurikulum)
    if len(a) > 5 and len(b) > 5:
        return _tanpa_spasi(a) == _tanpa_spasi(b)
    return False


#Token Subset

def cara4_token_subset(nama_khs: str, nama_kurikulum: str) -> bool:
    a = normalize_nama(nama_khs)
    b = normalize_nama(nama_kurikulum)
    tokens_a = set(a.split())
    tokens_b = set(b.split())
    shorter = tokens_a if len(tokens_a) <= len(tokens_b) else tokens_b
    longer  = tokens_b if len(tokens_a) <= len(tokens_b) else tokens_a
    return len(shorter) >= 2 and shorter.issubset(longer)


#Fuzzy

def cara5_fuzzy(nama_khs: str, nama_kurikulum: str) -> tuple[bool, float]:
    a = normalize_nama(nama_khs)
    b = normalize_nama(nama_kurikulum)
    if len(a) > 8 and len(b) > 8:
        ratio = SequenceMatcher(None, a, b).ratio()
        return ratio >= 0.88, round(ratio, 3)
    return False, 0.0


# Print

def baris(judul):
    print(f"\n  {judul}")
    print(f"  {'-' * len(judul)}")

def tampil(khs, kurikulum, hasil, keterangan=""):
    print(f"  KHS       : \"{khs}\"")
    print(f"  Kurikulum : \"{kurikulum}\"")
    print(f"  Hasil     : {'[COCOK]' if hasil else '[TIDAK COCOK]'}" +
          (f"  ({keterangan})" if keterangan else ""))
    print()


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":

    # --- CARA 1 ---
    baris("1. Exact Match (setelah normalisasi)")
    khs = "  ALGORITMA DAN PEMROGRAMAN  "
    kur = "Algoritma dan Pemrograman"
    hasil = cara1_exact(khs, kur)
    print(f"  normalize(\"{khs.strip()}\") -> \"{normalize_nama(khs)}\"")
    print(f"  normalize(\"{kur}\")         -> \"{normalize_nama(kur)}\"")
    print()
    tampil(khs.strip(), kur, hasil)

    # --- CARA 2 ---
    baris("2. Substring Dua Arah")
    khs = "Basis Data"
    kur = "Sistem Basis Data"
    # Pastikan cara 1 gagal dulu
    c1 = cara1_exact(khs, kur)
    c2 = cara2_substring(khs, kur)
    print(f"  Cara 1 (exact)     : {'[COCOK]' if c1 else '[GAGAL]'}")
    print(f"  Cara 2 (substring) : {'[COCOK]' if c2 else '[GAGAL]'}")
    print(f"  -> \"{normalize_nama(khs)}\" ada di dalam \"{normalize_nama(kur)}\" ? {normalize_nama(khs) in normalize_nama(kur)}")
    print()
    tampil(khs, kur, c2)

    # --- CARA 3 ---
    baris("3. Tanpa Spasi (word-break PDF)")
    khs = "Techno preneurship"
    kur = "Technopreneurship"
    c1 = cara1_exact(khs, kur)
    c2 = cara2_substring(khs, kur)
    c3 = cara3_tanpa_spasi(khs, kur)
    print(f"  Cara 1 (exact)      : {'[COCOK]' if c1 else '[GAGAL]'}")
    print(f"  Cara 2 (substring)  : {'[COCOK]' if c2 else '[GAGAL]'}")
    print(f"  Cara 3 (tanpa spasi): {'[COCOK]' if c3 else '[GAGAL]'}")
    print(f"  -> tanpa spasi KHS : \"{_tanpa_spasi(normalize_nama(khs))}\"")
    print(f"  -> tanpa spasi KUR : \"{_tanpa_spasi(normalize_nama(kur))}\"")
    print()
    tampil(khs, kur, c3)

    # --- CARA 4 ---
    baris("4. Token Subset (urutan kata berbeda)")
    khs = "Sistem Operasi"
    kur = "Operasi Sistem"
    c1 = cara1_exact(khs, kur)
    c2 = cara2_substring(khs, kur)
    c3 = cara3_tanpa_spasi(khs, kur)
    c4 = cara4_token_subset(khs, kur)
    a  = normalize_nama(khs)
    b  = normalize_nama(kur)
    print(f"  Cara 1 (exact)       : {'[COCOK]' if c1 else '[GAGAL]'}")
    print(f"  Cara 2 (substring)   : {'[COCOK]' if c2 else '[GAGAL]'}")
    print(f"  Cara 3 (tanpa spasi) : {'[COCOK]' if c3 else '[GAGAL]'}")
    print(f"  Cara 4 (token subset): {'[COCOK]' if c4 else '[GAGAL]'}")
    print(f"  -> token KHS : {set(a.split())}")
    print(f"  -> token KUR : {set(b.split())}")
    print(f"  -> subset?   : {set(a.split()).issubset(set(b.split()))}")
    print()
    tampil(khs, kur, c4)

    # --- CARA 5 ---
    baris("Fuzzy Matching (perbedaan ejaan kecil)")
    khs = "Pemograman Berorientasi Objek"
    kur = "Pemrograman Berorientasi Objek"
    c1 = cara1_exact(khs, kur)
    c2 = cara2_substring(khs, kur)
    c3 = cara3_tanpa_spasi(khs, kur)
    c4 = cara4_token_subset(khs, kur)
    c5, rasio = cara5_fuzzy(khs, kur)
    print(f"  Cara 1 (exact)       : {'[COCOK]' if c1 else '[GAGAL]'}")
    print(f"  Cara 2 (substring)   : {'[COCOK]' if c2 else '[GAGAL]'}")
    print(f"  Cara 3 (tanpa spasi) : {'[COCOK]' if c3 else '[GAGAL]'}")
    print(f"  Cara 4 (token subset): {'[COCOK]' if c4 else '[GAGAL]'}")
    print(f"  Cara 5 (fuzzy)       : {'[COCOK]' if c5 else '[GAGAL]'}  rasio = {rasio} (ambang batas >= 0.88)")
    print()
    tampil(khs, kur, c5, f"rasio={rasio}")

    # --- PERBANDINGAN DENGAN vs TANPA FUZZY ---
    baris("PERBANDINGAN: Tanpa Fuzzy vs Dengan Fuzzy")
    kasus = [
        ("Pemograman Berorientasi Objek",  "Pemrograman Berorientasi Objek"),
        ("Jarinagn Komputer",              "Jaringan Komputer"),
        ("Kecerdasaan Buatan",             "Kecerdasan Buatan"),
    ]
    print(f"  {'KHS (hasil OCR)':<35} {'Tanpa Fuzzy':<14} {'Dengan Fuzzy'}")
    print("  " + "-" * 58)
    for khs, kur in kasus:
        tanpa = cara1_exact(khs,kur) or cara2_substring(khs,kur) or \
                cara3_tanpa_spasi(khs,kur) or cara4_token_subset(khs,kur)
        dengan, rasio = cara5_fuzzy(khs, kur)
        dengan = tanpa or dengan  # cara 5 hanya jalan jika 1-4 gagal
        print(f"  {khs:<35} {'[COCOK]' if tanpa else '[TIDAK]':<14} {'[COCOK]' if dengan else '[TIDAK]'}",
              end="")
        if not tanpa and dengan:
            _, r = cara5_fuzzy(khs, kur)
            print(f"  (rasio={r})", end="")
        print()
    print()
    print("  Kesimpulan: kasus [TIDAK] tanpa fuzzy -> MK dianggap belum")
    print("  diambil meskipun sudah lulus, sehingga SKS tidak terhitung.")
