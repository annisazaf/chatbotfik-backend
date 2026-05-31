export interface PeminatanConfig {
  harus_konsisten: boolean;
  min_mk_per_jalur: number;
  jalur: Record<string, string>;
  keterangan?: string;
}

export interface MataKuliahItem {
  id: number;
  prodi_id: number;
  kode: string;
  nama: string;
  sks: number;
  semester: number;
  keterangan: string | null;
  prasyarat: string | null;
  urutan: number;
  updated_at: string | null;
}

export interface ProdiItem {
  id: number;
  nama_prodi: string;
  total_semester: number;
  sks_lulus: number;
  syarat_sidang_sks: number;
  is_active: boolean;
  peminatan_config: PeminatanConfig | null;
  total_mk: number;
  total_sks: number;
  created_at: string;
  updated_at: string | null;
  mata_kuliah?: MataKuliahItem[];
}

export interface MKPerSemester {
  [semester: number]: MataKuliahItem[];
}

export interface MKListResponse {
  prodi_id: number;
  nama_prodi: string;
  total_mk: number;
  total_sks: number;
  per_semester: MKPerSemester;
  mk: MataKuliahItem[];
}

// Form state untuk tambah/edit MK
export interface MKFormData {
  kode: string;
  nama: string;
  sks: string;
  semester: string;
  keterangan: string;
  prasyarat: string;
}

// Form state untuk tambah/edit Prodi
export interface ProdiFormData {
  nama_prodi: string;
  total_semester: string;
  sks_lulus: string;
  syarat_sidang_sks: string;
  is_active: boolean;
}

// Informasi chatbot
export interface PengetahuanItem {
  id: number;
  judul: string;
  konten: string;
  kategori: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string | null;
}

export interface PengetahuanFormData {
  judul: string;
  konten: string;
  kategori: string;
  is_active: boolean;
}
