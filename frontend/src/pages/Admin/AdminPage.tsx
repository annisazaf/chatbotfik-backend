import { useState, useEffect, useRef } from "react";
import { adminService } from "../../services/adminServices";
import { ProdiItem, MataKuliahItem, MKFormData, ProdiFormData, PengetahuanItem, PengetahuanFormData } from "../../types/admin";

const GREEN = "#307045";

const KETERANGAN_OPTIONS = [
  "", "MKWU", "MKPS", "MBKM", "PLPS", "Pilihan",
  "Peminatan CE.1", "Peminatan CE.2", "Peminatan CE.3",
  "Peminatan NE.1", "Peminatan NE.2", "Peminatan NE.3",
  "Peminatan SE.1", "Peminatan SE.2", "Peminatan SE.3",
  "Peminatan AU.1", "Peminatan AU.2", "Peminatan AU.3",
  "Peminatan AD.1", "Peminatan AD.2", "Peminatan AD.3",
  "Peminatan ES.1", "Peminatan ES.2", "Peminatan ES.3",
  "Peminatan DE.1", "Peminatan DE.2", "Peminatan DE.3",
  "Peminatan DA.1", "Peminatan DA.2", "Peminatan DA.3",
];

const EMPTY_MK: MKFormData = { kode: "", nama: "", sks: "3", semester: "1", keterangan: "", prasyarat: "" };
const EMPTY_PRODI: ProdiFormData = { nama_prodi: "", total_semester: "8", sks_lulus: "144", syarat_sidang_sks: "138", is_active: true };

interface UserItem {
  nim: string;
  nama: string;
  email: string;
  role: "mahasiswa" | "admin";
}

// ── Badge keterangan MK ──
function KetBadge({ ket }: { ket: string | null }) {
  if (!ket) return <span className="text-gray-300 text-xs">—</span>;
  const color = ket.startsWith("Peminatan") ? "#e8f5ed" : ket === "MKWU" ? "#fef3c7" : ket === "MKPS" ? "#dbeafe" : ket === "MBKM" ? "#fce7f3" : "#f3f4f6";
  const textColor = ket.startsWith("Peminatan") ? GREEN : ket === "MKWU" ? "#92400e" : ket === "MKPS" ? "#1e40af" : ket === "MBKM" ? "#9d174d" : "#374151";
  return <span className="text-xs px-2 py-0.5 rounded-full font-medium" style={{ backgroundColor: color, color: textColor }}>{ket}</span>;
}

// ── Modal MK ──
function MKModal({ mode, mk, prodiId, maxSemester, onSave, onClose }: {
  mode: "tambah" | "edit"; mk?: MataKuliahItem; prodiId: number; maxSemester: number; onSave: () => void; onClose: () => void;
}) {
  const [form, setForm] = useState<MKFormData>(
    mk ? { kode: mk.kode || "", nama: mk.nama, sks: String(mk.sks), semester: String(mk.semester), keterangan: mk.keterangan || "", prasyarat: mk.prasyarat || "" }
       : EMPTY_MK
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async () => {
    if (!form.nama.trim()) return setError("Nama mata kuliah wajib diisi.");
    if (!form.sks || parseInt(form.sks) <= 0) return setError("SKS harus lebih dari 0.");
    setLoading(true); setError("");
    try {
      if (mode === "tambah") await adminService.tambahMK(prodiId, form);
      else if (mk) await adminService.editMK(mk.id, form);
      onSave(); onClose();
    } catch (e: unknown) {
      const err = e as { response?: { data?: { error?: string } } };
      setError(err.response?.data?.error || "Gagal menyimpan.");
    } finally { setLoading(false); }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center" onClick={onClose}>
      <div className="absolute inset-0 bg-black/30" />
      <div className="relative bg-white rounded-2xl shadow-xl w-full max-w-md mx-4 p-6 flex flex-col gap-4" onClick={e => e.stopPropagation()}>
        <h3 className="text-lg font-bold text-gray-800">{mode === "tambah" ? "Tambah Mata Kuliah" : "Edit Mata Kuliah"}</h3>
        {error && <div className="bg-red-50 border border-red-100 text-red-600 text-sm rounded-xl px-4 py-2">{error}</div>}
        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-gray-600">Kode MK</label>
            <input className="border border-gray-200 rounded-lg px-3 py-2 text-sm outline-none focus:border-green-400" placeholder="IF101" value={form.kode} onChange={e => setForm(f => ({ ...f, kode: e.target.value }))} />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-gray-600">SKS <span className="text-red-400">*</span></label>
            <input type="number" min="1" max="6" className="border border-gray-200 rounded-lg px-3 py-2 text-sm outline-none focus:border-green-400" value={form.sks} onChange={e => setForm(f => ({ ...f, sks: e.target.value }))} />
          </div>
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-gray-600">Nama Mata Kuliah <span className="text-red-400">*</span></label>
          <input className="border border-gray-200 rounded-lg px-3 py-2 text-sm outline-none focus:border-green-400" placeholder="Algoritma dan Pemrograman" value={form.nama} onChange={e => setForm(f => ({ ...f, nama: e.target.value }))} />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-gray-600">Semester <span className="text-red-400">*</span></label>
            <select className="border border-gray-200 rounded-lg px-3 py-2 text-sm outline-none focus:border-green-400 bg-white" value={form.semester} onChange={e => setForm(f => ({ ...f, semester: e.target.value }))}>
              {Array.from({ length: maxSemester }, (_, i) => i + 1).map(s => <option key={s} value={s}>Semester {s}</option>)}
            </select>
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-gray-600">Keterangan</label>
            <select className="border border-gray-200 rounded-lg px-3 py-2 text-sm outline-none focus:border-green-400 bg-white" value={form.keterangan} onChange={e => setForm(f => ({ ...f, keterangan: e.target.value }))}>
              {KETERANGAN_OPTIONS.map(k => <option key={k} value={k}>{k || "— tidak ada —"}</option>)}
            </select>
          </div>
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-gray-600">Prasyarat</label>
          <input className="border border-gray-200 rounded-lg px-3 py-2 text-sm outline-none focus:border-green-400" placeholder="Nama MK prasyarat (kosongkan jika tidak ada)" value={form.prasyarat} onChange={e => setForm(f => ({ ...f, prasyarat: e.target.value }))} />
        </div>
        <div className="flex gap-2 mt-1">
          <button onClick={onClose} className="flex-1 py-2.5 rounded-xl border border-gray-200 text-sm text-gray-500 hover:bg-gray-50">Batal</button>
          <button onClick={handleSubmit} disabled={loading} className="flex-1 py-2.5 rounded-xl text-white text-sm font-medium disabled:opacity-50" style={{ backgroundColor: GREEN }}>
            {loading ? "Menyimpan..." : "Simpan"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Modal Prodi ──
function ProdiModal({ mode, prodi, onSave, onClose }: { mode: "tambah" | "edit"; prodi?: ProdiItem; onSave: () => void; onClose: () => void; }) {
  const [form, setForm] = useState<ProdiFormData>(
    prodi ? { nama_prodi: prodi.nama_prodi, total_semester: String(prodi.total_semester), sks_lulus: String(prodi.sks_lulus), syarat_sidang_sks: String(prodi.syarat_sidang_sks), is_active: prodi.is_active }
          : EMPTY_PRODI
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async () => {
    if (!form.nama_prodi.trim()) return setError("Nama prodi wajib diisi.");
    setLoading(true); setError("");
    try {
      if (mode === "tambah") await adminService.tambahProdi(form);
      else if (prodi) await adminService.editProdi(prodi.id, form);
      onSave(); onClose();
    } catch (e: unknown) {
      const err = e as { response?: { data?: { error?: string } } };
      setError(err.response?.data?.error || "Gagal menyimpan.");
    } finally { setLoading(false); }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center" onClick={onClose}>
      <div className="absolute inset-0 bg-black/30" />
      <div className="relative bg-white rounded-2xl shadow-xl w-full max-w-sm mx-4 p-6 flex flex-col gap-4" onClick={e => e.stopPropagation()}>
        <h3 className="text-lg font-bold text-gray-800">{mode === "tambah" ? "Tambah Program Studi" : "Edit Program Studi"}</h3>
        {error && <div className="bg-red-50 border border-red-100 text-red-600 text-sm rounded-xl px-4 py-2">{error}</div>}
        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-gray-600">Nama Prodi <span className="text-red-400">*</span></label>
          <input className="border border-gray-200 rounded-lg px-3 py-2 text-sm outline-none focus:border-green-400" placeholder="S1 Informatika" value={form.nama_prodi} onChange={e => setForm(f => ({ ...f, nama_prodi: e.target.value }))} />
        </div>
        <div className="grid grid-cols-3 gap-2">
          {([["total_semester", "Total Semester"], ["sks_lulus", "SKS Lulus"], ["syarat_sidang_sks", "SKS Sidang"]] as const).map(([key, label]) => (
            <div key={key} className="flex flex-col gap-1">
              <label className="text-xs font-medium text-gray-600">{label}</label>
              <input type="number" className="border border-gray-200 rounded-lg px-3 py-2 text-sm outline-none focus:border-green-400" value={form[key]} onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))} />
            </div>
          ))}
        </div>
        <label className="flex items-center gap-2 cursor-pointer">
          <input type="checkbox" checked={form.is_active} onChange={e => setForm(f => ({ ...f, is_active: e.target.checked }))} className="w-4 h-4 accent-green-600" />
          <span className="text-sm text-gray-600">Prodi aktif</span>
        </label>
        <div className="flex gap-2 mt-1">
          <button onClick={onClose} className="flex-1 py-2.5 rounded-xl border border-gray-200 text-sm text-gray-500 hover:bg-gray-50">Batal</button>
          <button onClick={handleSubmit} disabled={loading} className="flex-1 py-2.5 rounded-xl text-white text-sm font-medium disabled:opacity-50" style={{ backgroundColor: GREEN }}>
            {loading ? "Menyimpan..." : "Simpan"}
          </button>
        </div>
      </div>
    </div>
  );
}

// Modal Konfirmasi Hapus
function ConfirmModal({ pesan, onConfirm, onClose }: { pesan: string; onConfirm: () => void; onClose: () => void; }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center" onClick={onClose}>
      <div className="absolute inset-0 bg-black/30" />
      <div className="relative bg-white rounded-2xl shadow-xl w-full max-w-sm mx-4 p-6 flex flex-col gap-4" onClick={e => e.stopPropagation()}>
        <h3 className="text-lg font-bold text-gray-800">Konfirmasi Hapus</h3>
        <p className="text-sm text-gray-500">{pesan}</p>
        <div className="flex gap-2">
          <button onClick={onClose} className="flex-1 py-2.5 rounded-xl border border-gray-200 text-sm text-gray-500 hover:bg-gray-50">Batal</button>
          <button onClick={onConfirm} className="flex-1 py-2.5 rounded-xl bg-red-500 text-white text-sm font-medium hover:bg-red-600">Hapus</button>
        </div>
      </div>
    </div>
  );
}

// Tab: Daftar Pengguna
type TabPenggunaProps = {
  currentNim: string;
};

function TabPengguna({ currentNim }: TabPenggunaProps) {
  const [users, setUsers]     = useState<UserItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch]   = useState("");
  const [roleFilter, setRoleFilter] = useState<"semua" | "mahasiswa" | "admin">("semua");
  const [roleLoading, setRoleLoading] = useState<string | null>(null);

  const handleUbahRole = async (nim: string, currentRole: string) => {
    const newRole = currentRole === "admin" ? "mahasiswa" : "admin";
    if (!window.confirm(`Ubah role ${nim} dari "${currentRole}" menjadi "${newRole}"?`)) return;
    setRoleLoading(nim);
    try {
    const res = await fetch(`${import.meta.env.VITE_API_URL || "http://localhost:5000/api"}/admin/users/${nim}/role`,{
      method: "PUT",
      credentials: "include",
      headers: {"Content-Type": "application/json",
      Authorization: `Bearer ${localStorage.getItem("chatbotfik_token") || ""}`,
    },
    body: JSON.stringify({ role: newRole }),
  }
);
      const data = await res.json();
      if (!res.ok) { alert(data.error || "Gagal mengubah role."); return; }
      setUsers(prev => prev.map(u => u.nim === nim ? { ...u, role: newRole as "admin" | "mahasiswa" } : u));
    } catch { alert("Gagal terhubung ke server."); }
    finally { setRoleLoading(null); }
  };

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
    const res = await fetch(`${import.meta.env.VITE_API_URL || "http://localhost:5000/api"}/admin/users`,{
      method: "GET",
      credentials: "include",
      headers: {
      Authorization: `Bearer ${localStorage.getItem("chatbotfik_token") || ""}`,
    },
  }
);        const data = await res.json();
        setUsers(data.users || []);
      } catch { setUsers([]); }
      finally { setLoading(false); }
    };
    load();
  }, []);

  const filtered = users
    .filter(u => roleFilter === "semua" || u.role === roleFilter)
    .filter(u => !search || u.nama.toLowerCase().includes(search.toLowerCase()) || u.nim.includes(search) || u.email.toLowerCase().includes(search.toLowerCase()));

  const totalMahasiswa = users.filter(u => u.role === "mahasiswa").length;
  const totalAdmin     = users.filter(u => u.role === "admin").length;

  return (
    <div className="flex-1 px-4 md:px-8 py-4 md:py-6 flex flex-col gap-5">

      {/* Stat cards */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: "Total Pengguna", value: users.length, color: GREEN, bg: "#e8f5ed" },
          { label: "Mahasiswa", value: totalMahasiswa, color: "#1e40af", bg: "#dbeafe" },
          { label: "Admin", value: totalAdmin, color: "#92400e", bg: "#fef3c7" },
        ].map(s => (
          <div key={s.label} className="bg-white rounded-2xl border border-gray-100 px-5 py-4 flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl flex items-center justify-center text-xl font-bold" style={{ backgroundColor: s.bg, color: s.color }}>
              {s.value}
            </div>
            <div>
              <p className="text-xs text-gray-400">{s.label}</p>
              <p className="text-lg font-bold text-gray-800">{s.value} orang</p>
            </div>
          </div>
        ))}
      </div>

      {/* Filter + search */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex items-center gap-2 bg-white border border-gray-200 rounded-xl px-3 py-2 flex-1 max-w-xs">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#aaa" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <input type="text" placeholder="Cari nama, NIM, atau email..." value={search} onChange={e => setSearch(e.target.value)} className="text-sm text-gray-600 outline-none bg-transparent w-full placeholder-gray-300" />
        </div>
        <div className="flex gap-1.5">
          {(["semua", "mahasiswa", "admin"] as const).map(r => (
            <button key={r} onClick={() => setRoleFilter(r)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-colors ${roleFilter === r ? "text-white" : "bg-white border border-gray-200 text-gray-500 hover:bg-gray-50"}`}
              style={roleFilter === r ? { backgroundColor: GREEN } : {}}>
              {r}
            </button>
          ))}
        </div>
        <span className="text-xs text-gray-400 ml-auto">{filtered.length} pengguna</span>
      </div>

      {/* Tabel */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="w-8 h-8 rounded-full border-2 border-t-transparent animate-spin" style={{ borderColor: GREEN, borderTopColor: "transparent" }} />
        </div>
      ) : filtered.length === 0 ? (
        <div className="flex items-center justify-center py-20 text-gray-400 text-sm">Tidak ada pengguna ditemukan.</div>
      ) : (
        <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden overflow-x-auto">
          <div className="grid grid-cols-12 px-5 py-3 border-b border-gray-100 bg-gray-50">
            <span className="col-span-1 text-xs font-semibold text-gray-400 uppercase">#</span>
            <span className="col-span-2 text-xs font-semibold text-gray-400 uppercase">NIM</span>
            <span className="col-span-3 text-xs font-semibold text-gray-400 uppercase">Nama</span>
            <span className="col-span-3 text-xs font-semibold text-gray-400 uppercase">Email</span>
            <span className="col-span-1 text-xs font-semibold text-gray-400 uppercase text-center">Role</span>
            <span className="col-span-2 text-xs font-semibold text-gray-400 uppercase text-center">Aksi</span>
          </div>
          {filtered.map((u, idx) => (
            <div key={u.nim} className={`grid grid-cols-12 px-5 py-3 items-center border-b border-gray-50 hover:bg-gray-50 transition-colors ${idx % 2 === 0 ? "" : "bg-gray-50/40"}`}>
              <span className="col-span-1 text-xs text-gray-400">{idx + 1}</span>
              <span className="col-span-2 text-sm font-mono text-gray-600">{u.nim}</span>
              <span className="col-span-3 text-sm font-medium text-gray-800">{u.nama}</span>
              <span className="col-span-3 text-xs text-gray-400 truncate pr-2">{u.email}</span>
              <span className="col-span-1 flex justify-center">
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${u.role === "admin" ? "bg-amber-50 text-amber-700" : "bg-green-50 text-green-700"}`}>
                  {u.role}
                </span>
              </span>
              <span className="col-span-2 flex justify-center">
                {u.nim !== currentNim ? (
                  <button
                    onClick={() => handleUbahRole(u.nim, u.role)}
                    disabled={roleLoading === u.nim}
                    className="px-2.5 py-1 rounded-lg text-xs font-medium border transition-colors disabled:opacity-40"
                    style={u.role === "admin"
                      ? { borderColor: "#fbbf24", color: "#92400e", backgroundColor: "#fffbeb" }
                      : { borderColor: "#6ee7b7", color: "#065f46", backgroundColor: "#f0fdf4" }
                    }
                  >
                    {roleLoading === u.nim ? "..." : u.role === "admin" ? "→ Mahasiswa" : "→ Admin"}
                  </button>
                ) : (
                  <span className="text-xs text-gray-300 italic">—</span>
                )}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Modal Pengetahuan Chatbot ──
const KATEGORI_OPTIONS = ["", "akademik", "karier", "umum", "prosedur", "jadwal", "lainnya"];
const EMPTY_PENGETAHUAN: PengetahuanFormData = { judul: "", konten: "", kategori: "", is_active: true };

function PengetahuanModal({ mode, item, onSave, onClose }: {
  mode: "tambah" | "edit"; item?: PengetahuanItem; onSave: () => void; onClose: () => void;
}) {
  const [form, setForm] = useState<PengetahuanFormData>(
    item
      ? { judul: item.judul, konten: item.konten, kategori: item.kategori || "", is_active: item.is_active }
      : EMPTY_PENGETAHUAN
  );
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState("");

  const handleSubmit = async () => {
    if (!form.judul.trim()) return setError("Judul wajib diisi.");
    if (!form.konten.trim()) return setError("Konten wajib diisi.");
    setLoading(true); setError("");
    try {
      if (mode === "tambah") await adminService.tambahPengetahuan(form);
      else if (item) await adminService.editPengetahuan(item.id, form);
      onSave(); onClose();
    } catch (e: unknown) {
      const err = e as { response?: { data?: { error?: string } } };
      setError(err.response?.data?.error || "Gagal menyimpan.");
    } finally { setLoading(false); }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center" onClick={onClose}>
      <div className="absolute inset-0 bg-black/30" />
      <div className="relative bg-white rounded-2xl shadow-xl w-full max-w-lg mx-4 p-6 flex flex-col gap-4" onClick={e => e.stopPropagation()}>
        <h3 className="text-lg font-bold text-gray-800">
          {mode === "tambah" ? "Tambah Informasi Chatbot" : "Edit Informasi Chatbot"}
        </h3>
        <p className="text-xs text-gray-400 -mt-2">Informasi ini akan otomatis muncul di konteks chatbot saat mahasiswa bertanya.</p>

        {error && <div className="bg-red-50 border border-red-100 text-red-600 text-sm rounded-xl px-4 py-2">{error}</div>}

        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-gray-600">Judul <span className="text-red-400">*</span></label>
          <input
            className="border border-gray-200 rounded-lg px-3 py-2 text-sm outline-none focus:border-green-400"
            placeholder="Contoh: Jadwal Pendaftaran KRS 2025/2026"
            value={form.judul}
            onChange={e => setForm(f => ({ ...f, judul: e.target.value }))}
          />
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-gray-600">Kategori</label>
          <select
            className="border border-gray-200 rounded-lg px-3 py-2 text-sm outline-none focus:border-green-400 bg-white"
            value={form.kategori}
            onChange={e => setForm(f => ({ ...f, kategori: e.target.value }))}
          >
            {KATEGORI_OPTIONS.map(k => <option key={k} value={k}>{k || "— pilih kategori —"}</option>)}
          </select>
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-gray-600">Konten Informasi <span className="text-red-400">*</span></label>
          <textarea
            rows={7}
            className="border border-gray-200 rounded-lg px-3 py-2 text-sm outline-none focus:border-green-400 resize-y font-mono"
            placeholder={"Tulis informasi yang ingin diketahui chatbot...\n\nContoh:\nPendaftaran KRS semester ganjil 2025/2026 dibuka mulai 1 Juli 2025.\nMahasiswa wajib konsultasi dengan dosen wali sebelum mengisi KRS.\nBatas maksimal SKS per semester: 24 SKS (IPK ≥ 3.0) atau 21 SKS (IPK < 3.0)."}
            value={form.konten}
            onChange={e => setForm(f => ({ ...f, konten: e.target.value }))}
          />
          <p className="text-xs text-gray-400">Tulis sejelas mungkin, chatbot akan menjawab berdasarkan teks ini.</p>
        </div>

        <label className="flex items-center gap-2 cursor-pointer">
          <input type="checkbox" checked={form.is_active} onChange={e => setForm(f => ({ ...f, is_active: e.target.checked }))} className="w-4 h-4 accent-green-600" />
          <span className="text-sm text-gray-600">Aktif (langsung digunakan chatbot)</span>
        </label>

        <div className="flex gap-2 mt-1">
          <button onClick={onClose} className="flex-1 py-2.5 rounded-xl border border-gray-200 text-sm text-gray-500 hover:bg-gray-50">Batal</button>
          <button onClick={handleSubmit} disabled={loading} className="flex-1 py-2.5 rounded-xl text-white text-sm font-medium disabled:opacity-50" style={{ backgroundColor: GREEN }}>
            {loading ? "Menyimpan..." : "Simpan"}
          </button>
        </div>
      </div>
    </div>
  );
}

// Tab: Pengetahuan Chatbot
function TabPengetahuan() {
  const [list, setList]         = useState<PengetahuanItem[]>([]);
  const [loading, setLoading]   = useState(true);
  const [modal, setModal]       = useState<{ mode: "tambah" | "edit"; item?: PengetahuanItem } | null>(null);
  const [confirmHapus, setConfirmHapus] = useState<PengetahuanItem | null>(null);
  const [togglingId, setTogglingId]     = useState<number | null>(null);
  const [search, setSearch]     = useState("");

  const load = async () => {
    setLoading(true);
    try { setList(await adminService.listPengetahuan()); }
    catch { setList([]); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const handleToggleAktif = async (item: PengetahuanItem) => {
    setTogglingId(item.id);
    try {
      await adminService.editPengetahuan(item.id, { is_active: !item.is_active });
      setList(prev => prev.map(p => p.id === item.id ? { ...p, is_active: !p.is_active } : p));
    } catch { /* abaikan */ }
    finally { setTogglingId(null); }
  };

  const handleHapus = async () => {
    if (!confirmHapus) return;
    try {
      await adminService.hapusPengetahuan(confirmHapus.id);
      setList(prev => prev.filter(p => p.id !== confirmHapus.id));
    } catch { /* abaikan */ }
    setConfirmHapus(null);
  };

  const filtered = list.filter(p =>
    !search || p.judul.toLowerCase().includes(search.toLowerCase()) || p.konten.toLowerCase().includes(search.toLowerCase())
  );

  const totalAktif = list.filter(p => p.is_active).length;

  const KATEGORI_COLOR: Record<string, { bg: string; text: string }> = {
    akademik:  { bg: "#dbeafe", text: "#1e40af" },
    karier:    { bg: "#fce7f3", text: "#9d174d" },
    umum:      { bg: "#f3f4f6", text: "#374151" },
    prosedur:  { bg: "#fef3c7", text: "#92400e" },
    jadwal:    { bg: "#e0e7ff", text: "#3730a3" },
    lainnya:   { bg: "#f0fdf4", text: "#166534" },
  };

  return (
    <div className="flex-1 px-4 md:px-8 py-4 md:py-6 flex flex-col gap-5">

      {/* Stat + tombol tambah */}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="bg-white rounded-2xl border border-gray-100 px-5 py-4 flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl flex items-center justify-center text-xl font-bold" style={{ backgroundColor: "#e8f5ed", color: GREEN }}>{list.length}</div>
          <div><p className="text-xs text-gray-400">Total Informasi</p><p className="text-lg font-bold text-gray-800">{list.length} entri</p></div>
        </div>
        <div className="bg-white rounded-2xl border border-gray-100 px-5 py-4 flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl flex items-center justify-center text-xl font-bold" style={{ backgroundColor: "#dcfce7", color: "#166534" }}>{totalAktif}</div>
          <div><p className="text-xs text-gray-400">Aktif (digunakan chatbot)</p><p className="text-lg font-bold text-gray-800">{totalAktif} entri</p></div>
        </div>
        <button
          onClick={() => setModal({ mode: "tambah" })}
          className="ml-auto px-4 py-2.5 rounded-xl text-white text-sm font-medium flex items-center gap-2"
          style={{ backgroundColor: GREEN }}
        >
          + Tambah Informasi
        </button>
      </div>

      {/* Info */}
      <div className="bg-blue-50 border border-blue-100 rounded-xl px-4 py-3 text-sm text-blue-700 flex items-start gap-2">
        <svg className="mt-0.5 shrink-0" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        <span>Pengetahuan yang aktif akan otomatis disertakan ke konteks chatbot.</span>
      </div>

      {/* Search */}
      <div className="flex items-center gap-2 bg-white border border-gray-200 rounded-xl px-3 py-2 max-w-sm">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#aaa" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        <input type="text" placeholder="Cari judul atau konten..." value={search} onChange={e => setSearch(e.target.value)} className="text-sm text-gray-600 outline-none bg-transparent w-full placeholder-gray-300" />
      </div>

      {/* List */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="w-8 h-8 rounded-full border-2 border-t-transparent animate-spin" style={{ borderColor: GREEN, borderTopColor: "transparent" }} />
        </div>
      ) : filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 gap-3 text-gray-400">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#d1d5db" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2a10 10 0 1 0 0 20A10 10 0 0 0 12 2z"/><path d="M12 8v4m0 4h.01"/></svg>
          <span className="text-sm">{search ? "Tidak ada hasil pencarian." : "Belum ada informasi. Klik \"+ Tambah Informasi\" untuk memulai."}</span>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {filtered.map(item => {
            const katColor = item.kategori ? (KATEGORI_COLOR[item.kategori] || KATEGORI_COLOR["lainnya"]) : null;
            return (
              <div key={item.id} className={`bg-white rounded-2xl border p-5 flex flex-col gap-3 transition-opacity ${item.is_active ? "border-gray-100" : "border-gray-100 opacity-60"}`}>
                <div className="flex items-start gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-semibold text-gray-800 text-sm">{item.judul}</span>
                      {katColor && item.kategori && (
                        <span className="text-xs px-2 py-0.5 rounded-full font-medium" style={{ backgroundColor: katColor.bg, color: katColor.text }}>{item.kategori}</span>
                      )}
                      {!item.is_active && <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-400 font-medium">non-aktif</span>}
                    </div>
                    <p className="text-xs text-gray-400 mt-0.5">Dibuat: {new Date(item.created_at).toLocaleDateString("id-ID")}</p>
                  </div>
                  <div className="flex items-center gap-1.5 shrink-0">
                    {/* Toggle aktif */}
                    <button
                      onClick={() => handleToggleAktif(item)}
                      disabled={togglingId === item.id}
                      title={item.is_active ? "Nonaktifkan" : "Aktifkan"}
                      className={`px-2.5 py-1 rounded-lg text-xs font-medium border transition-colors disabled:opacity-40 ${item.is_active ? "border-green-200 text-green-700 bg-green-50 hover:bg-green-100" : "border-gray-200 text-gray-500 bg-gray-50 hover:bg-gray-100"}`}
                    >
                      {togglingId === item.id ? "..." : item.is_active ? "✓ Aktif" : "Nonaktif"}
                    </button>
                    <button onClick={() => setModal({ mode: "edit", item })} className="w-7 h-7 rounded-lg border border-gray-200 flex items-center justify-center text-gray-400 hover:text-blue-500 hover:border-blue-200 transition-colors" title="Edit">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                    </button>
                    <button onClick={() => setConfirmHapus(item)} className="w-7 h-7 rounded-lg border border-gray-200 flex items-center justify-center text-gray-400 hover:text-red-400 hover:border-red-200 transition-colors" title="Hapus">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6M14 11v6"/></svg>
                    </button>
                  </div>
                </div>
                {/* Preview konten */}
                <div className="bg-gray-50 rounded-xl px-4 py-3 text-xs text-gray-600 font-mono whitespace-pre-wrap max-h-32 overflow-y-auto">
                  {item.konten}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {modal && (
        <PengetahuanModal mode={modal.mode} item={modal.item} onSave={load} onClose={() => setModal(null)} />
      )}
      {confirmHapus && (
        <ConfirmModal
          pesan={`Yakin hapus pengetahuan "${confirmHapus.judul}"? Tindakan ini tidak dapat dibatalkan.`}
          onConfirm={handleHapus}
          onClose={() => setConfirmHapus(null)}
        />
      )}
    </div>
  );
}

// Halaman utama admin
type ActiveTab = "kurikulum" | "pengguna" | "pengetahuan";

type AdminPageProps = {
  onLogout: () => void | Promise<void>;
  currentNim: string;
};

export default function AdminPage({ onLogout, currentNim }: AdminPageProps) {
  const [activeTab, setActiveTab]         = useState<ActiveTab>("kurikulum");
  const [prodiList, setProdiList]         = useState<ProdiItem[]>([]);
  const [selectedProdi, setSelectedProdi] = useState<ProdiItem | null>(null);
  const [mkList, setMkList]               = useState<MataKuliahItem[]>([]);
  const [semesterAktif, setSemesterAktif] = useState<number | "all">("all");
  const [loading, setLoading]             = useState(true);
  const [loadingMK, setLoadingMK]         = useState(false);
  const [search, setSearch]               = useState("");

  const [modalMK, setModalMK]           = useState<{ mode: "tambah" | "edit"; mk?: MataKuliahItem } | null>(null);
  const [modalProdi, setModalProdi]     = useState<{ mode: "tambah" | "edit"; prodi?: ProdiItem } | null>(null);
  const [confirmHapus, setConfirmHapus] = useState<{ type: "prodi" | "mk"; id: number; nama: string } | null>(null);
  const [importLoading, setImportLoading] = useState(false);
  const [importMsg, setImportMsg]         = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadProdi = async () => {
    setLoading(true);
    try {
      const list = await adminService.listProdi();
      setProdiList(list);
      if (!selectedProdi && list.length > 0) setSelectedProdi(list[0]);
    } catch { /* abaikan */ }
    finally { setLoading(false); }
  };

  const loadMK = async (prodiId: number) => {
    setLoadingMK(true);
    try {
      const res = await adminService.listMK(prodiId);
      setMkList(res.mk);
    } catch { setMkList([]); }
    finally { setLoadingMK(false); }
  };

  useEffect(() => { loadProdi(); }, []);
  useEffect(() => {
    if (selectedProdi) { setSemesterAktif("all"); setSearch(""); loadMK(selectedProdi.id); }
  }, [selectedProdi]);

  const handleHapus = async () => {
    if (!confirmHapus) return;
    try {
      if (confirmHapus.type === "mk") {
        await adminService.hapusMK(confirmHapus.id);
        if (selectedProdi) loadMK(selectedProdi.id);
      } else {
        await adminService.hapusProdi(confirmHapus.id);
        setSelectedProdi(null); loadProdi();
      }
    } catch { /* abaikan */ }
    setConfirmHapus(null);
  };

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !selectedProdi) return;
    setImportLoading(true); setImportMsg("");
    try {
      const res = await adminService.importXLSX(file, selectedProdi.id);
      setImportMsg(`✓ ${res.message} (${res.total_mk} MK, ${res.total_sks} SKS)`);
      loadMK(selectedProdi.id); loadProdi();
    } catch (e: unknown) {
      const err = e as { response?: { data?: { error?: string } } };
      setImportMsg(`✗ ${err.response?.data?.error || "Gagal import."}`);
    } finally {
      setImportLoading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const mkFiltered = mkList
    .filter(mk => semesterAktif === "all" || mk.semester === semesterAktif)
    .filter(mk => !search || mk.nama.toLowerCase().includes(search.toLowerCase()) || (mk.kode || "").toLowerCase().includes(search.toLowerCase()));

  const semesterList = [...new Set(mkList.map(mk => mk.semester))].sort((a, b) => a - b);

  return (
    <div className="min-h-screen flex" style={{ backgroundColor: "#f8f9fa" }}>

      {/* ── SIDEBAR ── */}
      <aside className="fixed top-0 left-0 bottom-0 w-60 flex flex-col bg-white border-r border-gray-100 z-30">
        <div className="px-5 py-6 border-b border-gray-100">
          <div className="flex items-center gap-2 mb-1">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center text-white text-xs font-bold" style={{ backgroundColor: GREEN }}>A</div>
            <span className="font-bold text-gray-800 text-sm">Admin Panel</span>
          </div>
          <p className="text-xs text-gray-400">Manajemen Kurikulum FIK</p>
        </div>

        {/* Tab navigasi */}
        <div className="px-3 py-3 border-b border-gray-100 flex flex-col gap-1">
          {([
            { key: "kurikulum",   label: "Kurikulum",   icon: "M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" },
            { key: "pengetahuan", label: "Informasi", icon: "M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" },
            { key: "pengguna",    label: "Pengguna",    icon: "M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" },
          ] as const).map(tab => (
            <button key={tab.key} onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-2.5 px-3 py-2 rounded-xl text-sm font-medium transition-colors ${activeTab === tab.key ? "text-emerald-700 bg-green-50" : "text-gray-500 hover:bg-gray-50"}`}>
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d={tab.icon}/></svg>
              {tab.label}
            </button>
          ))}
        </div>

        {/* List prodi (hanya tampil di tab kurikulum) */}
        {activeTab === "kurikulum" && (
          <div className="flex-1 overflow-y-auto py-3 px-3">
            <p className="text-xs font-semibold text-gray-400 px-2 mb-2 uppercase tracking-wide">Program Studi</p>
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <div className="w-5 h-5 rounded-full border-2 border-t-transparent animate-spin" style={{ borderColor: GREEN, borderTopColor: "transparent" }} />
              </div>
            ) : prodiList.map(prodi => (
              <button key={prodi.id} onClick={() => setSelectedProdi(prodi)}
                className={`w-full text-left px-3 py-2.5 rounded-xl mb-1 transition-colors ${selectedProdi?.id === prodi.id ? "text-emerald-700" : "text-gray-600 hover:bg-gray-50"}`}
                style={selectedProdi?.id === prodi.id ? { backgroundColor: "#e8f5ed" } : {}}>
                <div className="text-sm font-medium leading-tight">{prodi.nama_prodi}</div>
                <div className="text-xs text-gray-400 mt-0.5">{prodi.total_mk} MK · {prodi.total_sks} SKS</div>
                {!prodi.is_active && <span className="text-xs text-red-400">non-aktif</span>}
              </button>
            ))}
          </div>
        )}

        {(activeTab === "pengguna" || activeTab === "pengetahuan") && <div className="flex-1" />}

        <div className="px-3 py-4 border-t border-gray-100 flex flex-col gap-2">
          {activeTab === "kurikulum" && (
            <button onClick={() => setModalProdi({ mode: "tambah" })} className="w-full py-2 rounded-xl text-white text-xs font-medium" style={{ backgroundColor: GREEN }}>
              + Tambah Prodi
            </button>
          )}
          <button onClick={onLogout} className="w-full py-2 rounded-xl border border-gray-200 text-xs text-gray-500 hover:bg-gray-50">Logout</button>
        </div>
      </aside>

      {/* ── KONTEN ── */}
      <main className="ml-60 flex-1 flex flex-col">

        {/* Header */}
        <div className="bg-white border-b border-gray-100 px-8 py-5 flex items-center justify-between sticky top-0 z-20">
          <div>
            {activeTab === "pengguna" ? (
              <h1 className="text-xl font-bold text-gray-800">Daftar Pengguna</h1>
            ) : activeTab === "pengetahuan" ? (
              <>
                <h1 className="text-xl font-bold text-gray-800">Informasi Chatbot</h1>
                <p className="text-xs text-gray-400 mt-0.5">Kelola informasi yang digunakan FIKA untuk menjawab pertanyaan mahasiswa</p>
              </>
            ) : selectedProdi ? (
              <>
                <h1 className="text-xl font-bold text-gray-800">{selectedProdi.nama_prodi}</h1>
                <p className="text-xs text-gray-400 mt-0.5">{selectedProdi.total_mk} MK · {selectedProdi.total_sks} SKS · Sidang min. {selectedProdi.syarat_sidang_sks} SKS</p>
              </>
            ) : (
              <h1 className="text-xl font-bold text-gray-800">Pilih Program Studi</h1>
            )}
          </div>

          {activeTab === "kurikulum" && selectedProdi && (
            <div className="flex items-center gap-2">
              <button onClick={() => setModalProdi({ mode: "edit", prodi: selectedProdi })} className="px-3 py-2 rounded-xl border border-gray-200 text-xs text-gray-600 hover:bg-gray-50 flex items-center gap-1.5">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                Edit Prodi
              </button>
              <button onClick={() => setConfirmHapus({ type: "prodi", id: selectedProdi.id, nama: selectedProdi.nama_prodi })} className="px-3 py-2 rounded-xl border border-red-100 text-xs text-red-500 hover:bg-red-50 flex items-center gap-1.5">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6M14 11v6"/><path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/></svg>
                Hapus Prodi
              </button>
              <a href="/template_kurikulum.xlsx" download className="px-3 py-2 rounded-xl border border-gray-200 text-xs text-gray-600 hover:bg-gray-50 flex items-center gap-1.5 no-underline" style={{ textDecoration: "none", color: "inherit" }}>
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                Template XLSX
              </a>
              <button onClick={() => fileInputRef.current?.click()} disabled={importLoading} className="px-3 py-2 rounded-xl border border-blue-100 text-xs text-blue-600 hover:bg-blue-50 flex items-center gap-1.5 disabled:opacity-50">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                {importLoading ? "Mengimpor..." : "Import XLSX"}
              </button>
              <input ref={fileInputRef} type="file" accept=".xlsx" className="hidden" onChange={handleImport} />
              <button onClick={() => setModalMK({ mode: "tambah" })} className="px-4 py-2 rounded-xl text-white text-xs font-medium flex items-center gap-1.5" style={{ backgroundColor: GREEN }}>
                + Tambah MK
              </button>
            </div>
          )}
        </div>

        {importMsg && (
          <div className={`mx-8 mt-4 px-4 py-2.5 rounded-xl text-sm ${importMsg.startsWith("✓") ? "bg-green-50 text-green-700 border border-green-100" : "bg-red-50 text-red-600 border border-red-100"}`}>
            {importMsg}
            <button onClick={() => setImportMsg("")} className="ml-3 opacity-50 hover:opacity-100">✕</button>
          </div>
        )}

        {/* ── Tab: Pengguna ── */}
        {activeTab === "pengguna" && <TabPengguna currentNim={currentNim} />}

        {/* ── Tab: Pengetahuan ── */}
        {activeTab === "pengetahuan" && <TabPengetahuan />}

        {/* ── Tab: Kurikulum ── */}
        {activeTab === "kurikulum" && selectedProdi && (
          <div className="flex-1 px-8 py-6 flex flex-col gap-4">
            <div className="flex items-center gap-3 flex-wrap">
              <div className="flex items-center gap-2 bg-white border border-gray-200 rounded-xl px-3 py-2 flex-1 max-w-xs">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#aaa" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                <input type="text" placeholder="Cari nama atau kode MK..." value={search} onChange={e => setSearch(e.target.value)} className="text-sm text-gray-600 outline-none bg-transparent w-full placeholder-gray-300" />
              </div>
              <div className="flex items-center gap-1.5 flex-wrap">
                <button onClick={() => setSemesterAktif("all")} className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${semesterAktif === "all" ? "text-white" : "bg-white border border-gray-200 text-gray-500 hover:bg-gray-50"}`} style={semesterAktif === "all" ? { backgroundColor: GREEN } : {}}>Semua</button>
                {semesterList.map(s => (
                  <button key={s} onClick={() => setSemesterAktif(s)} className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${semesterAktif === s ? "text-white" : "bg-white border border-gray-200 text-gray-500 hover:bg-gray-50"}`} style={semesterAktif === s ? { backgroundColor: GREEN } : {}}>Sem {s}</button>
                ))}
              </div>
              <span className="text-xs text-gray-400 ml-auto">{mkFiltered.length} mata kuliah</span>
            </div>

            {loadingMK ? (
              <div className="flex items-center justify-center py-20">
                <div className="w-8 h-8 rounded-full border-2 border-t-transparent animate-spin" style={{ borderColor: GREEN, borderTopColor: "transparent" }} />
              </div>
            ) : mkFiltered.length === 0 ? (
              <div className="flex items-center justify-center py-20 text-gray-400 text-sm">{search ? "Tidak ada hasil." : "Belum ada mata kuliah."}</div>
            ) : (
              <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
                <div className="grid grid-cols-12 px-5 py-3 border-b border-gray-100 bg-gray-50">
                  <span className="col-span-1 text-xs font-semibold text-gray-400 uppercase">Sem</span>
                  <span className="col-span-1 text-xs font-semibold text-gray-400 uppercase">Kode</span>
                  <span className="col-span-4 text-xs font-semibold text-gray-400 uppercase">Nama Mata Kuliah</span>
                  <span className="col-span-1 text-xs font-semibold text-gray-400 uppercase text-center">SKS</span>
                  <span className="col-span-2 text-xs font-semibold text-gray-400 uppercase">Keterangan</span>
                  <span className="col-span-2 text-xs font-semibold text-gray-400 uppercase">Prasyarat</span>
                  <span className="col-span-1 text-xs font-semibold text-gray-400 uppercase text-center">Aksi</span>
                </div>
                {mkFiltered.map((mk, idx) => (
                  <div key={mk.id} className={`grid grid-cols-12 px-5 py-3 items-center border-b border-gray-50 hover:bg-gray-50 transition-colors ${idx % 2 === 0 ? "" : "bg-gray-50/40"}`}>
                    <span className="col-span-1 text-xs font-semibold text-gray-400">{mk.semester}</span>
                    <span className="col-span-1 text-xs text-gray-400 font-mono">{mk.kode || "—"}</span>
                    <span className="col-span-4 text-sm text-gray-700 font-medium pr-4">{mk.nama}</span>
                    <span className="col-span-1 text-sm font-bold text-center" style={{ color: GREEN }}>{mk.sks}</span>
                    <span className="col-span-2"><KetBadge ket={mk.keterangan} /></span>
                    <span className="col-span-2 text-xs text-gray-400">{mk.prasyarat || "—"}</span>
                    <span className="col-span-1 flex items-center justify-center gap-1">
                      <button onClick={() => setModalMK({ mode: "edit", mk })} className="w-7 h-7 rounded-lg border border-gray-200 flex items-center justify-center text-gray-400 hover:text-blue-500 hover:border-blue-200 transition-colors" title="Edit">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                      </button>
                      <button onClick={() => setConfirmHapus({ type: "mk", id: mk.id, nama: mk.nama })} className="w-7 h-7 rounded-lg border border-gray-200 flex items-center justify-center text-gray-400 hover:text-red-400 hover:border-red-200 transition-colors" title="Hapus">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6M14 11v6"/></svg>
                      </button>
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === "kurikulum" && !selectedProdi && !loading && (
          <div className="flex-1 flex items-center justify-center text-gray-400 text-sm">Pilih program studi dari sidebar.</div>
        )}
      </main>

      {/* MODALS */}
      {modalMK && selectedProdi && (
        <MKModal mode={modalMK.mode} mk={modalMK.mk} prodiId={selectedProdi.id} maxSemester={selectedProdi.total_semester} onSave={() => loadMK(selectedProdi.id)} onClose={() => setModalMK(null)} />
      )}
      {modalProdi && (
        <ProdiModal mode={modalProdi.mode} prodi={modalProdi.prodi} onSave={() => { loadProdi(); if (modalProdi.prodi) setSelectedProdi(null); }} onClose={() => setModalProdi(null)} />
      )}
      {confirmHapus && (
        <ConfirmModal pesan={`Yakin hapus ${confirmHapus.type === "mk" ? "mata kuliah" : "program studi"} "${confirmHapus.nama}"? Tindakan ini tidak dapat dibatalkan.`} onConfirm={handleHapus} onClose={() => setConfirmHapus(null)} />
      )}
    </div>
  );
}
