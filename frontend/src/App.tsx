import { useEffect, useState } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { authService } from "./services/authServices";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import ForgotPasswordPage from "./pages/ForgotPasswordPage";
import ResetPasswordPage from "./pages/ResetPasswordPage";
import HomePage from "./pages/Dashboard/HomePage";
import AdminPage from "./pages/Admin/AdminPage";
import { Loader2 } from "lucide-react";

interface AuthUser {
  nim: string;
  nama: string;
  role: "mahasiswa" | "admin";
}

function App() {
  const [user, setUser]     = useState<AuthUser | null | undefined>(undefined);
  // undefined = masih loading, null = belum login, object = sudah login

  const checkAuth = async () => {
    try {
      const data = await authService.getMe();
      setUser(data as AuthUser);
    } catch {
      setUser(null);
    }
  };

  const handleLogout = async () => {
    await authService.logout();
    setUser(null);
  };

  useEffect(() => { checkAuth(); }, []);

  // Loading spinner
  if (user === undefined) {
    return (
      <div className="flex h-screen w-full flex-col items-center justify-center bg-slate-50 gap-3">
        <Loader2 className="h-10 w-10 animate-spin text-[#307045]" />
        <p className="text-sm font-medium text-slate-500">Memeriksa Sesi...</p>
      </div>
    );
  }

  const isAuth  = user !== null;
  const isAdmin = user?.role === "admin";

  return (
    <Router>
      <Routes>
        {/* Login */}
        <Route
          path="/login"
          element={
            !isAuth
              ? <LoginPage onLoginSuccess={checkAuth} />
              : <Navigate to={isAdmin ? "/admin" : "/home"} replace />
          }
        />

        {/* Register */}
        <Route
          path="/register"
          element={
            !isAuth ? <RegisterPage /> : <Navigate to={isAdmin ? "/admin" : "/home"} replace />
          }
        />

        {/* Lupa password */}
        <Route
          path="/forgot-password"
          element={!isAuth ? <ForgotPasswordPage /> : <Navigate to={isAdmin ? "/admin" : "/home"} replace />}
        />

        {/* Reset password (via link email) */}
        <Route path="/reset-password" element={<ResetPasswordPage />} />

        {/* Dashboard mahasiswa */}
        <Route
          path="/home"
          element={
            !isAuth   ? <Navigate to="/login" replace /> :
            isAdmin   ? <Navigate to="/admin" replace /> :
            <HomePage onLogout={handleLogout} user={user!} />
          }
        />

        {/* Dashboard admin */}
        <Route
          path="/admin"
          element={
            !isAuth  ? <Navigate to="/login" replace /> :
            !isAdmin ? <Navigate to="/home" replace /> :
            <AdminPage onLogout={handleLogout} currentNim={user?.nim ?? ""} />
          }
        />

        {/* Fallback */}
        <Route path="/" element={<Navigate to={isAuth ? (isAdmin ? "/admin" : "/home") : "/login"} replace />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </Router>
  );
}

export default App;