import { useEffect, useState } from "react";
import logo from "../../assets/logo.svg";
import { RiwayatItem } from "../../types/chat";
import { tokenStorage } from "../../services/authServices";

const API = import.meta.env.VITE_API_URL || "http://localhost:5000/api";

function authHeaders(): Record<string, string> {
  const token = tokenStorage.get();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

interface RiwayatModalProps {
  onClose?: () => void;
  onMulaiChat?: () => void;
  onLanjutChat?: (sessionId: string) => void;
}

function timeAgo(isoString: string): string {
  const diff = Date.now() - new Date(isoString).getTime();
  const mins  = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days  = Math.floor(diff / 86400000);
  const weeks = Math.floor(days / 7);
  if (mins < 60)  return `${mins}m ago`;
  if (hours < 24) return `${hours}h ago`;
  if (days < 7)   return `${days}d ago`;
  return `${weeks}w ago`;
}

export default function RiwayatModal({ onClose, onMulaiChat, onLanjutChat }: RiwayatModalProps) {
  const [items, setItems]       = useState<RiwayatItem[]>([]);
  const [filtered, setFiltered] = useState<RiwayatItem[]>([]);
  const [search, setSearch]     = useState("");
  const [loading, setLoading]   = useState(true);

  useEffect(() => {
    fetch(`${API}/chatbot/sessions`, { headers: authHeaders() })
      .then((r) => r.json())
      .then((d) => {
        const mapped: RiwayatItem[] = (d.sessions ?? []).map((s: {
          session_id: string; title: string; last_active: string; message_count: number;
        }) => ({
          session_id:    s.session_id,
          title:         s.title || "Chat tanpa judul",
          preview:       `${s.message_count} pesan`,
          last_active:   s.last_active,
          message_count: s.message_count,
        }));
        setItems(mapped);
        setFiltered(mapped);
      })
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, []);

  const handleSearch = (val: string) => {
    setSearch(val);
    setFiltered(items.filter((i) => i.title.toLowerCase().includes(val.toLowerCase())));
  };

  const handleDelete = async (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    await fetch(`${API}/chatbot/sessions/${sessionId}`, {
      method: "DELETE",
      headers: authHeaders(),
    });
    const next = items.filter((i) => i.session_id !== sessionId);
    setItems(next);
    setFiltered(next.filter((i) => i.title.toLowerCase().includes(search.toLowerCase())));
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-end" onClick={onClose}>
      <div className="absolute inset-0 bg-black/20" />
      <div className="relative bg-white shadow-xl w-72 flex flex-col overflow-hidden h-full" onClick={(e) => e.stopPropagation()}>

        <div className="px-5 pt-6 pb-3">
          <h2 className="text-xl font-bold text-gray-800">Riwayat Chat</h2>
        </div>

        <div className="px-5 pb-3">
          <div className="flex items-center gap-2 bg-gray-100 rounded-xl px-3 py-2">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#aaa" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
            <input type="text" placeholder="Cari..." value={search} onChange={(e) => handleSearch(e.target.value)}
              className="bg-transparent text-sm text-gray-600 placeholder-gray-400 outline-none w-full" />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-5 pb-4 flex flex-col">
          {loading ? (
            <div className="flex items-center justify-center py-10">
              <div className="w-6 h-6 rounded-full border-2 border-t-transparent animate-spin" style={{ borderColor: "#307045", borderTopColor: "transparent" }} />
            </div>
          ) : filtered.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-10">
              {search ? "Tidak ada hasil." : "Belum ada riwayat chat."}
            </p>
          ) : filtered.map((item, idx) => (
            <div key={item.session_id}>
              <button
                className="group flex items-center gap-3 w-full text-left py-3 hover:bg-gray-50 rounded-xl transition-colors px-1"
                onClick={() => { onLanjutChat?.(item.session_id); onClose?.(); }}
              >
                <div className="w-10 h-10 rounded-full bg-gray-100 flex-shrink-0 flex items-center justify-center">
                  <img src={logo} alt="logo" className="w-7 h-7 object-contain" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-gray-800 truncate">{item.title}</p>
                  <p className="text-xs text-gray-400 truncate">{item.preview}</p>
                </div>
                <div className="flex flex-col items-end gap-1 flex-shrink-0">
                  <span className="text-xs text-gray-400">{timeAgo(item.last_active)}</span>
                  <button onClick={(e) => handleDelete(e, item.session_id)}
                    className="opacity-0 group-hover:opacity-100 transition-opacity text-gray-300 hover:text-red-400 text-xs" title="Hapus sesi">
                    ✕
                  </button>
                </div>
              </button>
              {idx < filtered.length - 1 && <div className="h-px bg-gray-100 mx-1" />}
            </div>
          ))}
        </div>

        <div className="px-5 pb-6 pt-2">
          <button onClick={onMulaiChat} className="w-full py-3.5 rounded-2xl text-white text-sm font-semibold transition-colors" style={{ backgroundColor: "#307045" }}>
            Mulai chat baru
          </button>
        </div>
      </div>
    </div>
  );
}
