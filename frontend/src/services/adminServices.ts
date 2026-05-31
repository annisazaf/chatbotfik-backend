import { api } from "./api";
import {
  ProdiItem,
  MataKuliahItem,
  MKListResponse,
  MKFormData,
  ProdiFormData,
  PengetahuanItem,
  PengetahuanFormData,
} from "../types/admin";

export const adminService = {
  // ── Cek admin ──
  checkAdmin: async () => {
    const res = await api.get("/admin/check");
    return res.data;
  },

  // ── PRODI ──
  listProdi: async (): Promise<ProdiItem[]> => {
    const res = await api.get("/admin/prodi");
    return res.data.prodi || [];
  },

  getProdi: async (id: number): Promise<ProdiItem> => {
    const res = await api.get(`/admin/prodi/${id}`);
    return res.data;
  },

  tambahProdi: async (data: ProdiFormData): Promise<ProdiItem> => {
    const res = await api.post("/admin/prodi", {
      nama_prodi: data.nama_prodi,
      total_semester: parseInt(data.total_semester),
      sks_lulus: parseInt(data.sks_lulus),
      syarat_sidang_sks: parseInt(data.syarat_sidang_sks),
      is_active: data.is_active,
    });
    return res.data.prodi;
  },

  editProdi: async (
    id: number,
    data: Partial<ProdiFormData>
  ): Promise<ProdiItem> => {
    const payload: Record<string, unknown> = {};

    if (data.nama_prodi !== undefined) payload.nama_prodi = data.nama_prodi;
    if (data.total_semester !== undefined)
      payload.total_semester = parseInt(data.total_semester);
    if (data.sks_lulus !== undefined)
      payload.sks_lulus = parseInt(data.sks_lulus);
    if (data.syarat_sidang_sks !== undefined)
      payload.syarat_sidang_sks = parseInt(data.syarat_sidang_sks);
    if (data.is_active !== undefined) payload.is_active = data.is_active;

    const res = await api.put(`/admin/prodi/${id}`, payload);
    return res.data.prodi;
  },

  hapusProdi: async (id: number): Promise<void> => {
    await api.delete(`/admin/prodi/${id}`);
  },

  // ── MATA KULIAH ──
  listMK: async (prodiId: number): Promise<MKListResponse> => {
    const res = await api.get(`/admin/prodi/${prodiId}/mk`);
    return res.data;
  },

  tambahMK: async (
    prodiId: number,
    data: MKFormData
  ): Promise<MataKuliahItem> => {
    const res = await api.post("/admin/mk", {
      prodi_id: prodiId,
      kode: data.kode,
      nama: data.nama,
      sks: parseInt(data.sks),
      semester: parseInt(data.semester),
      keterangan: data.keterangan || null,
      prasyarat: data.prasyarat || null,
    });
    return res.data.mk;
  },

  editMK: async (
    mkId: number,
    data: Partial<MKFormData>
  ): Promise<MataKuliahItem> => {
    const payload: Record<string, unknown> = {};

    if (data.kode !== undefined) payload.kode = data.kode;
    if (data.nama !== undefined) payload.nama = data.nama;
    if (data.sks !== undefined) payload.sks = parseInt(data.sks);
    if (data.semester !== undefined) payload.semester = parseInt(data.semester);
    if (data.keterangan !== undefined)
      payload.keterangan = data.keterangan || null;
    if (data.prasyarat !== undefined)
      payload.prasyarat = data.prasyarat || null;

    const res = await api.put(`/admin/mk/${mkId}`, payload);
    return res.data.mk;
  },

  hapusMK: async (mkId: number): Promise<void> => {
    await api.delete(`/admin/mk/${mkId}`);
  },

  // ── PENGETAHUAN CHATBOT ──
  listPengetahuan: async (): Promise<PengetahuanItem[]> => {
    const res = await api.get("/admin/pengetahuan");
    return res.data.pengetahuan || [];
  },

  tambahPengetahuan: async (data: PengetahuanFormData): Promise<PengetahuanItem> => {
    const res = await api.post("/admin/pengetahuan", {
      judul:     data.judul,
      konten:    data.konten,
      kategori:  data.kategori || null,
      is_active: data.is_active,
    });
    return res.data.pengetahuan;
  },

  editPengetahuan: async (id: number, data: Partial<PengetahuanFormData>): Promise<PengetahuanItem> => {
    const payload: Record<string, unknown> = {};
    if (data.judul     !== undefined) payload.judul     = data.judul;
    if (data.konten    !== undefined) payload.konten    = data.konten;
    if (data.kategori  !== undefined) payload.kategori  = data.kategori || null;
    if (data.is_active !== undefined) payload.is_active = data.is_active;
    const res = await api.put(`/admin/pengetahuan/${id}`, payload);
    return res.data.pengetahuan;
  },

  hapusPengetahuan: async (id: number): Promise<void> => {
    await api.delete(`/admin/pengetahuan/${id}`);
  },

  // ── IMPORT XLSX ──
  importXLSX: async (
    file: File,
    prodiId?: number
  ): Promise<{ message: string; total_mk: number; total_sks: number }> => {
    const formData = new FormData();
    formData.append("file", file);

    if (prodiId) {
      formData.append("prodi_id", String(prodiId));
    }

    const res = await api.post("/admin/import-xlsx", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });

    return res.data;
  },
};