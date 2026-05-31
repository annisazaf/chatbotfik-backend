import React, { useState } from "react";
import { Link } from "react-router-dom";
import { authService } from "@/services/authServices";
import { Input } from "@/components/ui/input";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, AlertCircle, CheckCircle2 } from "lucide-react";
import logoFika from "@/assets/logo.png";
import "./auth.css";

const Logo = () => <img src={logoFika} alt="FIKA" style={{ width: 38, height: 38, objectFit: "contain" }} />;

export default function ForgotPasswordPage() {
  const [email, setEmail]     = useState("");
  const [error, setError]     = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await authService.forgotPassword(email.trim().toLowerCase());
      setSuccess(true);
    } catch (err: any) {
      setError(err.response?.data?.error || "Terjadi kesalahan. Coba lagi.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <nav className="auth-navbar">
        <div className="auth-navbar__brand"><Logo />ChatbotFIK</div>
      </nav>

      <div className="auth-hero" style={{ minHeight: "100vh", alignItems: "center", justifyContent: "center" }}>
        <div className="auth-hero__blob" style={{ top: -100, right: -100, width: 500, height: 500 }} />
        <div className="auth-hero__blob" style={{ bottom: 80, left: -80, width: 350, height: 350 }} />

        <div className="auth-card" style={{ maxWidth: 420, width: "100%", margin: "0 auto" }}>
          <div className="auth-card__header">
            <div className="auth-card__logo-wrap"><Logo /></div>
            <h2 className="auth-card__title">Lupa Password?</h2>
            <p className="auth-card__desc">
              Masukkan email yang terdaftar, untuk mereset password.
            </p>
          </div>

          {success ? (
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 12, padding: "8px 0 16px" }}>
              <CheckCircle2 style={{ width: 48, height: 48, color: "#307045" }} />
              <p style={{ textAlign: "center", color: "#374151", fontSize: 14 }}>
                Jika email <strong>{email}</strong> terdaftar, link reset password sudah dikirim.<br />
                Cek inbox (dan folder spam) kamu.
              </p>
              <Link to="/login" className="auth-form__link" style={{ marginTop: 8 }}>
                Kembali ke halaman login
              </Link>
            </div>
          ) : (
            <>
              {error && (
                <Alert variant="destructive" style={{ marginBottom: 16, borderRadius: 10 }}>
                  <AlertCircle style={{ width: 16, height: 16 }} />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <form onSubmit={handleSubmit} className="auth-form">
                <div>
                  <label className="auth-form__label">Email</label>
                  <Input
                    className="auth-form__input"
                    type="email"
                    placeholder="email@upnvj.ac.id"
                    value={email}
                    onChange={e => { setEmail(e.target.value); setError(null); }}
                    required
                  />
                </div>
                <button type="submit" disabled={loading} className="auth-form__btn">
                  {loading
                    ? <><Loader2 style={{ width: 18, height: 18, animation: "spin 1s linear infinite" }} /> Mengirim...</>
                    : "Kirim Link Reset"}
                </button>
              </form>

              <p className="auth-form__footer">
                Ingat password?{" "}
                <Link to="/login" className="auth-form__link">Masuk di sini</Link>
              </p>
            </>
          )}
        </div>
      </div>

      <div className="auth-footer">© 2026 Annisa Zhafira Adhya · Sistem Konseling Akademik & Karier Mahasiswa</div>
      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
