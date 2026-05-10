# ATURAN SKS KELULUSAN & BEBAN PER SEMESTER

ATURAN_PRODI = {
    "D3 Sistem Informasi": {
        "total_semester": 6,
        "sks_lulus": 108,
        "sks_per_semester": {1: 20, 2: 20, 3: 22, 4: 22, 5: 22, 6: 8},
        "syarat_sidang_sks": 100,
    },
    "S1 Sistem Informasi": {
        "total_semester": 8,
        "sks_lulus": 144,
        "sks_per_semester": {1: 19, 2: 19, 3: 20, 4: 22, 5: 21, 6: 20, 7: 19, 8: 4},
        "syarat_sidang_sks": 138,
    },
    "S1 Sains Data": {
        "total_semester": 8,
        "sks_lulus": 144,
        "sks_per_semester": {1: 20, 2: 20, 3: 22, 4: 21, 5: 19, 6: 20, 7: 18, 8: 4},
        "syarat_sidang_sks": 138,
    },
    "S1 Informatika": {
        "total_semester": 8,
        "sks_lulus": 144,
        "sks_per_semester": {1: 20, 2: 20, 3: 24, 4: 23, 5: 24, 6: 19, 7: 10, 8: 4},
        "syarat_sidang_sks": 138,
    },
}

# KETERANGAN JENIS MATAKULIAH

KETERANGAN_MK = {
    "MKWU": {
        "nama_lengkap": "Mata Kuliah Wajib Universitas",
        "deskripsi": "Wajib diambil seluruh mahasiswa UPN. Berkaitan dengan nilai kebangsaan, agama, dan karakter.",
        "contoh": ["Pendidikan Agama", "Pancasila", "Bahasa Indonesia",
                   "Pendidikan Bela Negara", "Kepemimpinan",
                   "Kewarganegaraan", "Filsafat Ilmu dan Logika"],
        "wajib": True,
    },
    "MKPS": {
        "nama_lengkap": "Mata Kuliah Wajib Fakultas dan Wajib Prodi",
        "deskripsi": "Wajib diambil mahasiswa FIK. Fondasi ilmu komputer yang relevan untuk semua prodi.",
        "wajib": True,
    },
    "MBKM": {
        "nama_lengkap": "Merdeka Belajar Kampus Merdeka",
        "deskripsi": "Kegiatan belajar di luar prodi, maksimal 3 semester (20 SKS/semester).",
        "wajib": False,
        "bentuk": [
            "Pertukaran Pelajar (IISMA / Pertukaran Mahasiswa Merdeka)",
            "Magang / Praktik Kerja",
            "Asistensi Mengajar di Satuan Pendidikan",
            "Penelitian / Riset",
            "Proyek Kemanusiaan",
            "Wirausaha Merdeka",
            "Studi Independen Bersertifikat",
            "Membangun Desa / KKN Tematik",
            "Bela Negara",
        ],
    },
    "PLPS": {
        "nama_lengkap": "Pembelajaran di Luar Program Studi",
        "deskripsi": "Mata kuliah dari prodi/fakultas lain di UPN. SKS tetap diakui dalam total kelulusan.",
        "wajib": False,
    },
    "Peminatan": {
        "nama_lengkap": "Mata Kuliah Peminatan",
        "deskripsi": "Diambil sesuai jalur peminatan yang dipilih mahasiswa.",
        "wajib": False,
    },
    "Pilihan": {
        "nama_lengkap": "Mata Kuliah Pilihan",
        "deskripsi": "Opsional, bebas dipilih dari daftar yang disediakan prodi.",
        "wajib": False,
    },
}

# ATURAN PEMINATAN PER PRODI

PEMINATAN_PRODI = {
    "D3 Sistem Informasi": {
        "keterangan": "Tidak ada jalur peminatan spesifik. Mahasiswa boleh ambil MK pilihan di semester 4.",
        "jalur": [],
        "min_mk_per_jalur": 0,
        "harus_konsisten": False,
    },
    "S1 Sistem Informasi": {
        "keterangan": "Pilih salah satu jalur peminatan, minimal 3 MK dalam jalur yang sama.",
        "jalur": {
            "AU": "Audit Sistem Informasi",
            "AD": "Application Development",
            "ES": "Supply Chain Analytics",
        },
        "min_mk_per_jalur": 3,
        "harus_konsisten": True,
    },
    "S1 Sains Data": {
        "keterangan": "Pilih salah satu jalur peminatan, minimal 3 MK dalam jalur yang sama.",
        "jalur": {
            "DE": "Data Engineering",
            "DA": "Data Analytics",
        },
        "min_mk_per_jalur": 3,
        "harus_konsisten": True,
    },
    "S1 Informatika": {
        "keterangan": "Pilih salah satu jalur peminatan, minimal 3 MK dalam jalur yang sama.",
        "jalur": {
            "CE": "Cybersecurity",
            "NE": "Network",
            "SE": "Software Engineering",
        },
        "min_mk_per_jalur": 3,
        "harus_konsisten": True,
    },
}

# ATURAN SKPI (SURAT KETERANGAN PENDAMPING IJAZAH)

ATURAN_SKPI = {
    "deskripsi": (
        "SKPI adalah dokumen resmi yang menyertai ijazah dan mencatat capaian mahasiswa "
        "di luar akademik. Wajib dipenuhi sebagai syarat kelulusan."
    ),
    "syarat": [
        {
            "nomor": 1,
            "judul": "Minimal 5 Sertifikat Kegiatan",
            "deskripsi": (
                "Mahasiswa wajib memiliki minimal 5 sertifikat dari kegiatan non-akademik. "
                "Sertifikat dapat berasal dari:"
            ),
            "kategori": [
                "Webinar",
                "Seminar",
                "Pelatihan / Workshop",
                "Lomba / Kompetisi",
                "Kejuaraan (tingkat program studi, fakultas, universitas, nasional, atau internasional)",
            ],
            "wajib": True,
            "min_jumlah": 5,
        },
        {
            "nomor": 2,
            "judul": "Lolos Program Kreativitas Mahasiswa (PKM) Tingkat Universitas",
            "deskripsi": (
                "Mahasiswa wajib pernah mengikuti dan lolos seleksi PKM "
                "minimal di tingkat universitas (UPNVJ)."
            ),
            "kategori": [
                "PKM-RE (Riset Eksakta)",
                "PKM-RSH (Riset Sosial Humaniora)",
                "PKM-PM (Pengabdian kepada Masyarakat)",
                "PKM-PI (Penerapan IPTEK)",
                "PKM-K (Kewirausahaan)",
                "PKM-KC (Karsa Cipta)",
                "PKM-GFT (Gagasan Futuristik Tertulis)",
                "PKM-VGK (Video Gagasan Konstruktif)",
            ],
            "wajib": True,
            "min_jumlah": 1,
        },
        {
            "nomor": 3,
            "judul": "Sertifikat Keahlian / Profesi",
            "deskripsi": (
                "Mahasiswa wajib memiliki minimal 1 sertifikat keahlian atau profesi "
                "yang diakui dari lembaga resmi yang bekerja sama dengan UPNVJ."
            ),
            "lembaga_diakui": [
                "BNSP (Badan Nasional Sertifikasi Profesi)",
                "LSP UPNVJ (Lembaga Sertifikasi Profesi UPN Veteran Jakarta)",
                "Hactiv8",
                "IBM",
                "Certiport",
                "Lembaga lain yang memiliki MoU resmi dengan UPNVJ",
            ],
            "wajib": True,
            "min_jumlah": 1,
        },
        {
            "nomor": 4,
            "judul": "Sertifikat TOEFL / ELPT",
            "deskripsi": (
                "Mahasiswa wajib memiliki sertifikat kemampuan bahasa Inggris "
                "dengan skor minimal 450."
            ),
            "jenis_tes": [
                "TOEFL ITP",
                "TOEFL iBT",
                "ELPT (English Language Proficiency Test) UPNVJ",
            ],
            "skor_minimal": 450,
            "wajib": True,
            "min_jumlah": 1,
        },
    ],
}


# ATURAN MBKM PER NIM

def get_semester_mbkm(nim: str) -> int:
    """
    Digit terakhir NIM Ganjil (semester 5), Genap (semester 6)
    """
    try:
        digit_terakhir = int(str(nim).strip()[-1])
        return 5 if digit_terakhir % 2 != 0 else 6
    except (ValueError, IndexError):
        return 5  # default semester 5