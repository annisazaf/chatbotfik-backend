import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { authService, type RegisterRequest } from "@/services/authServices";
import { Input } from "@/components/ui/input";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, AlertCircle } from "lucide-react";
import logoFika from "@/assets/logo.png";
import "./auth.css";

const Logo = () => <img src={logoFika} alt="FIKA" style={{ width: 38, height: 38, objectFit: "contain" }} />;

const NAV_ITEMS = ["Beranda", "Upload KHS", "Konseling", "Rekomendasi", "Riwayat"];
const FEATURES = [
  { emoji: "🧠", title: "Berbasis NLP & DeepSeek AI", desc: "Menggunakan teknologi NLP DeepSeek AI untuk memahami pertanyaan mahasiswa dan memberikan jawaban yang kontekstual dan personal." },
  { emoji: "📊", title: "Analisis Data Akademik Otomatis", desc: "Sistem membaca dan menganalisis file KHS secara otomatis menggunakan OCR untuk mengekstrak data nilai, IPK, IPS, dan mata kuliah yang telah ditempuh." },
  { emoji: "📚", title: "Validasi Prasyarat Mata Kuliah", desc: "Rekomendasi mata kuliah dihasilkan berdasarkan rule-based system yang memvalidasi prasyarat kurikulum sehingga hanya mata kuliah yang dapat diambil yang direkomendasikan." },
  { emoji: "🚀", title: "Rekomendasi Karier Personal", desc: "Menyediakan rekomendasi mata kuliah berdasarkan data akademik mahasiswa, dengan validasi prasyarat kurikulum. Selain itu juga menganalisis potensi karier berdasarkan performa studi dan minat mahasiswa. Seluruh riwayat konseling tersimpan dengan aman sehingga dapat diakses kembali kapan saja, serta didukung respons real-time 24/7." },
];
const STEPS = [
  { step: "01", title: "Daftar",         emoji: "📝", desc: "Buat akun menggunakan NIM, nama lengkap, email, dan password untuk mengakses layanan." },
  { step: "02", title: "Upload KHS",     emoji: "📄", desc: "Unggah KHS terbaru dalam format PDF agar sistem dapat membaca dan menganalisis data akademikmu." },
  { step: "03", title: "Mulai Konseling",emoji: "💬", desc: "Setelah proses analisis selesai, mulai percakapan di menu Konseling untuk diskusi rencana KRS." },
  { step: "04", title: "Akses Riwayat", emoji: "📋", desc: "Buka kembali menu Riwayat untuk melihat dan meninjau hasil diskusi sebelumnya kapan saja." },
];
const FIELDS: { key: keyof RegisterRequest; label: string; type?: string; placeholder: string }[] = [
  { key: "nim",      label: "NIM",          placeholder: "Contoh: 2021001234" },
  { key: "nama",     label: "Nama Lengkap", placeholder: "Nama sesuai KTM" },
  { key: "email",    label: "Email",        type: "email", placeholder: "nim@mahasiswa.upnvj.ac.id" },
  { key: "password", label: "Password",     type: "password", placeholder: "••••••••" },
];

export default function RegisterPage() {
  const [formData, setFormData] = useState<RegisterRequest>({ 
  nim: "", 
  nama: "", 
  email: "", 
  password: "",
  role: "mahasiswa",
 });
  const [error, setError]       = useState<string | null>(null);
  const [loading, setLoading]   = useState(false);
  const navigate = useNavigate();

  const handleChange = (field: keyof RegisterRequest) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({ ...prev, [field]: e.target.value }));
    setError(null);
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await authService.register(formData);
      navigate("/login");
    } catch (err: any) {
      setError(err.response?.data?.error || "Registrasi gagal. Coba lagi.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">

      {/* NAVBAR */}
      <nav className="auth-navbar">
        <div className="auth-navbar__brand"><Logo />ChatbotFIK</div>
        <div className="auth-navbar__links">
          {NAV_ITEMS.map(item => (
            <span key={item}
              onClick={item !== "Beranda" ? () => alert("Silakan login terlebih dahulu.") : undefined}
              className={`auth-navbar__link ${item === "Beranda" ? "auth-navbar__link--active" : ""}`}>
              {item}
            </span>
          ))}
        </div>
      </nav>

      {/* HERO */}
      <div className="auth-hero">
        <div className="auth-hero__blob" style={{ top: -100, right: -100, width: 500, height: 500 }} />
        <div className="auth-hero__blob" style={{ bottom: 80, left: -80, width: 350, height: 350 }} />

        <div className="auth-hero__content auth-hero__content--register">
          {/* Kiri */}
          <div>
            <p className="auth-hero__eyebrow">Fakultas Ilmu Komputer</p>
            <h1 className="auth-hero__title">Asisten Konseling Akademik & Karier Mahasiswa FIK</h1>
            <p className="auth-hero__subtitle">Membantu Mahasiswa FIK UPN "Veteran" Jakarta Merencanakan Studi Secara Terarah</p>
          </div>

          {/* Kanan: form register */}
          <div className="auth-card auth-card--register">
            <div className="auth-card__header auth-card__header--register">
              <div className="auth-card__logo-wrap"><Logo /></div>
              <h2 className="auth-card__title">Buat Akun Baru</h2>
              <p className="auth-card__desc">Lengkapi data diri untuk mulai menggunakan chatbot</p>
            </div>

            {error && (
              <Alert variant="destructive" style={{ marginBottom: 16, borderRadius: 10 }}>
                <AlertCircle style={{ width: 16, height: 16 }} />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <form onSubmit={handleRegister} className="auth-form auth-form--register">
              {FIELDS.map(f => (
                <div key={f.key}>
                  <label className="auth-form__label">{f.label}</label>
                  <Input className="auth-form__input" type={f.type || "text"} placeholder={f.placeholder}
                    value={formData[f.key]} onChange={handleChange(f.key)}
                    required autoComplete={f.key === "password" ? "new-password" : undefined} />
                </div>
              ))}
              <button type="submit" disabled={loading} className="auth-form__btn">
                {loading ? <><Loader2 style={{ width: 18, height: 18, animation: "spin 1s linear infinite" }} /> Mendaftarkan...</> : "Daftar Sekarang"}
              </button>
            </form>

            <p className="auth-form__footer">
              Sudah punya akun?{" "}
              <Link to="/login" className="auth-form__link">Masuk di sini</Link>
            </p>
          </div>
        </div>
      </div>

      {/* FIKA CHAT */}
      <div className="auth-chat-section">
        <div className="auth-chat-section__inner">
          <div className="auth-chat-section__row">
            <div className="auth-chat-section__avatar"><Logo /></div>
            <div className="auth-chat-section__bubbles">
              <div className="auth-bubble">
                <p className="auth-bubble__name">Halo, saya FIKA 👋</p>
                <p className="auth-bubble__tagline">Asisten Konseling Akademik dan Karier Mahasiswa FIK UPN "Veteran" Jakarta.</p>
              </div>
              <div className="auth-bubble">
                <p className="auth-bubble__body">Upload KHS-mu, diskusikan rencana KRS, atau tanyakan jalur karier yang cocok untukmu. Aku akan membantumu dengan analisis berbasis data dan AI agar keputusan studimu lebih tepat dan terarah.</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* FITUR */}
      <div className="auth-features-section">
        <div className="auth-features-section__inner">
          <h2 className="auth-section-title">Fitur Unggulan Sistem</h2>
          <p className="auth-section-divider">━━━━━━</p>
          {FEATURES.map((f, i) => (
            <div key={i} className="auth-feature-card auth-feature-card--hover">
              <span className="auth-feature-card__emoji">{f.emoji}</span>
              <div>
                <div className="auth-feature-card__title">{f.title}</div>
                <p className="auth-feature-card__desc auth-feature-card__desc--tooltip">{f.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* CARA PAKAI */}
      <div className="auth-steps-section">
        <div className="auth-steps-section__inner">
          <h2 className="auth-section-title">Cara Penggunaan</h2>
          <p className="auth-section-divider auth-section-divider--sm">━━━━━━</p>
          <div className="auth-steps-fika">
            <div className="auth-steps-fika__avatar"><Logo /></div>
            <p className="auth-steps-fika__bubble">Untuk menggunakan sistem ini secara optimal, silakan ikuti langkah berikut</p>
          </div>
          <div className="auth-steps-row">
            {STEPS.map((s, i) => (
              <div key={i} className="auth-step-card">
                <div className="auth-step-card__number">{s.step}</div>
                <div className="auth-step-card__emoji">{s.emoji}</div>
                <div className="auth-step-card__title">{s.title}</div>
                <p className="auth-step-card__desc">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* FOOTER */}
      <div className="auth-footer">© 2026 Annisa Zhafira Adhya · Sistem Konseling Akademik & Karier Mahasiswa</div>

      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
