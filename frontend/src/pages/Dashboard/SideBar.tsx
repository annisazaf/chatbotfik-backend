import { useState } from "react";
import logo from "../../assets/logo.svg";

const HomeIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M3 9.5L12 3l9 6.5V20a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9.5z"/>
    <path d="M9 21V12h6v9"/>
  </svg>
);

const UploadIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
    <polyline points="17 8 12 3 7 8"/>
    <line x1="12" y1="3" x2="12" y2="15"/>
  </svg>
);

const KonselingIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
  </svg>
);

const RekomendasiIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
    <circle cx="9" cy="7" r="4"/>
    <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
    <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
  </svg>
);

const RiwayatIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"/>
    <polyline points="12 6 12 12 16 14"/>
  </svg>
);

const MenuIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="3" y1="6" x2="21" y2="6"/>
    <line x1="3" y1="12" x2="21" y2="12"/>
    <line x1="3" y1="18" x2="21" y2="18"/>
  </svg>
);

const CloseIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" y1="6" x2="6" y2="18"/>
    <line x1="6" y1="6" x2="18" y2="18"/>
  </svg>
);

interface NavItem {
  key: string;
  label: string;
  icon: React.ReactNode;
  isModal?: boolean;
}

const navItems: NavItem[] = [
  { key: "beranda",     label: "Beranda",     icon: <HomeIcon /> },
  { key: "upload-khs",  label: "Upload KHS",  icon: <UploadIcon />,      isModal: true },
  { key: "konseling",   label: "Konseling",   icon: <KonselingIcon /> },
  { key: "rekomendasi", label: "Rekomendasi", icon: <RekomendasiIcon />, isModal: true },
  { key: "riwayat",     label: "Riwayat",     icon: <RiwayatIcon />,     isModal: true },
];

interface User {
  name: string;
  nim: string;
  avatar?: string | null;
}

interface SidebarProps {
  activeKey?: string;
  onNavigate?: (key: string) => void;
  onLogout?: () => void;
  user?: User;
  onShowUploadModal: () => void;
  onShowRekomendasiModal: () => void;
  onShowRiwayatModal: () => void;
  activeModal?: "upload" | "rekomendasi" | "riwayat" | null;
}

export default function Sidebar({
  activeKey = "beranda",
  onNavigate,
  onLogout,
  user,
  onShowUploadModal,
  onShowRekomendasiModal,
  onShowRiwayatModal,
  activeModal,
}: SidebarProps) {
  const [active, setActive] = useState<string>(activeKey);
  const [mobileOpen, setMobileOpen] = useState(false);

  const currentUser: User = user ?? {
    name: "Pengguna",
    nim: "-",
    avatar: null,
  };

  const handleNav = (item: NavItem) => {
    if (item.isModal) {
      if (item.key === "upload-khs")  onShowUploadModal();
      if (item.key === "rekomendasi") onShowRekomendasiModal();
      if (item.key === "riwayat")     onShowRiwayatModal();
      setMobileOpen(false);
      return;
    }
    setActive(item.key);
    onNavigate?.(item.key);
    setMobileOpen(false);
  };

  const sidebarContent = (
    <>
      {/* Logo */}
      <div className="flex justify-center mb-8">
        <img src={logo} alt="Logo" className="w-24 h-24 object-contain" />
      </div>

      {/* Nav */}
      <nav className="flex flex-col justify-center gap-1 flex-1">
        {navItems.map((item) => {
          const modalKeyMap: Record<string, string> = {
            "upload":      "upload-khs",
            "rekomendasi": "rekomendasi",
            "riwayat":     "riwayat",
          };
          const isActive =
            activeModal != null
              ? item.isModal && modalKeyMap[activeModal] === item.key
              : !item.isModal && active === item.key;

          return (
            <button
              key={item.key}
              onClick={() => handleNav(item)}
              className={`flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm font-medium w-full text-left transition-colors ${
                isActive
                  ? "text-emerald-700 bg-white/40"
                  : "text-gray-600 hover:bg-white/30 hover:text-gray-800"
              }`}
            >
              {item.icon}
              {item.label}
            </button>
          );
        })}
      </nav>

      {/* User Card */}
      <div className="mt-auto pt-4">
        <div
          className="rounded-xl p-3 flex flex-col gap-3"
          style={{
            background:
              "linear-gradient(white, #FCFBFC) padding-box, linear-gradient(135deg, #a8edea, #fed6e3, #ffecd2, #a1c4fd) border-box",
            border: "2.5px solid transparent",
          }}
        >
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-full bg-gray-400 overflow-hidden flex-shrink-0 flex items-center justify-center text-white text-sm font-semibold">
              {currentUser.avatar ? (
                <img src={currentUser.avatar} alt={currentUser.name} className="w-full h-full object-cover" />
              ) : (
                currentUser.name.charAt(0)
              )}
            </div>
            <div className="flex flex-col leading-tight">
              <span className="text-xs font-semibold text-gray-800">{currentUser.name}</span>
              <span className="text-xs text-gray-600">{currentUser.nim}</span>
            </div>
          </div>

          <button
            onClick={onLogout}
            className="w-full py-1.5 rounded-lg border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 transition-colors"
          >
            Logout
          </button>
        </div>
      </div>
    </>
  );

  return (
    <>
      {/* ── MOBILE TOP BAR ── */}
      <div
        className="md:hidden fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-4 py-3"
        style={{ backgroundColor: "#FCFBFC", borderBottom: "1px solid #e5e7eb", height: 56 }}
      >
        <img src={logo} alt="Logo" className="w-8 h-8 object-contain" />
        <span className="text-sm font-bold" style={{ color: "#307045" }}>ChatbotFIK</span>
        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          className="p-1 text-gray-600"
        >
          {mobileOpen ? <CloseIcon /> : <MenuIcon />}
        </button>
      </div>

      {/* ── MOBILE DRAWER OVERLAY ── */}
      {mobileOpen && (
        <div
          className="md:hidden fixed inset-0 z-40 bg-black/30"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* ── MOBILE DRAWER ── */}
      <aside
        className={`md:hidden fixed top-0 left-0 bottom-0 w-64 flex flex-col px-4 py-7 z-50 transition-transform duration-300 ${
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        }`}
        style={{ backgroundColor: "#FCFBFC", paddingTop: 72 }}
      >
        {sidebarContent}
      </aside>

      {/* ── DESKTOP SIDEBAR ── */}
      <aside
        className="hidden md:flex fixed top-0 left-0 bottom-0 w-56 flex-col px-4 py-7 z-40"
        style={{ backgroundColor: "#FCFBFC", border: "1.5px solid transparent" }}
      >
        {sidebarContent}
      </aside>
    </>
  );
}
