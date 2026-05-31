import { useState, useRef, useEffect } from "react";
import Sidebar from "./SideBar";
import bgImage from "../../assets/Background.png";
import iconNlp from "../../assets/icon-nlp.png";
import iconAnalisis from "../../assets/icon-analisis.png";
import iconMataKuliah from "../../assets/icon-matakuliah.png";
import iconKarier from "../../assets/icon-karier.png";
import logo from "../../assets/logo.svg";

import ChatInput from "../../components/Chat/ChatInput";
import ChatBubble from "../../components/Chat/ChatBubble";
import TypingIndicator from "../../components/Chat/TypingIndicator";
import UploadKHSModal from "../Dashboard/Uploadkhsmodal";
import RekomendasiModal from "../Dashboard/RekomendasiModal";
import RiwayatModal from "../Dashboard/RiwayatModal";
import { useChat } from "../../hooks/useChat";
import { FeatureCard } from "../../types/chat";

type ActiveModal = "upload" | "rekomendasi" | "riwayat" | null;

const features: FeatureCard[] = [
  { icon: iconNlp,        title: "Berbasis NLP & AI",           desc: "Respons konseling cerdas berbasis pemrosesan bahasa alami." },
  { icon: iconAnalisis,   title: "Analisis Akademik Otomatis",  desc: "Rekomendasi studi dari data KHS mahasiswa." },
  { icon: iconMataKuliah, title: "Rekomendasi Mata Kuliah",     desc: "Rekomendasi mata kuliah sesuai dengan kurikulum FIK." },
  { icon: iconKarier,     title: "Rekomendasi Karier Personal", desc: "Saran karier berdasarkan potensi akademik Anda." },
];

interface HomePageProps {
  onLogout: () => void;
  user: { nim: string; nama: string; role: string };
}

export default function HomePage({ onLogout, user }: HomePageProps) {
  const [activeNav, setActiveNav]     = useState<string>("beranda");
  const [message, setMessage]         = useState<string>("");
  const [activeModal, setActiveModal] = useState<ActiveModal>(null);

  const chatEndRef = useRef<HTMLDivElement>(null);
  const isKonseling = activeNav === "konseling";

  const { messages, sessionId, khsResult, isReplying, sendMessage, onKHSSuccess, loadSession } = useChat();

  useEffect(() => {
    if (isKonseling) chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isKonseling]);

  const handleSend = () => {
    if (!message.trim()) return;
    sendMessage(message);
    setMessage("");
    setActiveNav("konseling");
  };

  const closeModal = () => setActiveModal(null);

  return (
    <div className="flex min-h-screen">
      <Sidebar
        activeKey={activeNav}
        onNavigate={(key) => setActiveNav(key)}
        onShowUploadModal={() => setActiveModal("upload")}
        onShowRekomendasiModal={() => setActiveModal("rekomendasi")}
        onShowRiwayatModal={() => setActiveModal("riwayat")}
        activeModal={activeModal}
        onLogout={onLogout}
        user={{ name: user.nama, nim: user.nim }}
      />

      {/* main: on mobile pt-14 for topbar, on desktop ml-56 */}
      <main
        className="flex-1 relative flex flex-col min-h-screen pt-14 md:pt-0 md:ml-56"
        style={{
          backgroundImage: `url(${bgImage})`,
          backgroundSize: "cover",
          backgroundPosition: "center",
          backgroundAttachment: "fixed",
        }}
      >

        {/* ── BERANDA ── */}
        {!isKonseling && (
          <div className="relative z-10 flex flex-col items-center justify-between flex-1 min-h-screen px-4 md:px-10">
            <div className="flex flex-col items-center justify-center flex-1 gap-6 md:gap-10 pt-10 pb-6 md:pt-16 md:pb-8 w-full">
              <div className="flex flex-col items-center gap-3 text-center">
                <img src={logo} alt="Logo" className="w-16 h-16 md:w-20 md:h-20 object-contain" />
                <h1 className="text-2xl md:text-3xl font-bold mt-1" style={{ color: "#307045" }}>
                  Selamat Datang, FIKERS!
                </h1>
                <p className="text-gray-500 text-sm">Siap merencanakan studi dan kariermu?</p>
              </div>

              {/* Feature cards: 2 col on mobile, 4 col on desktop */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4 w-full max-w-3xl">
                {features.map((f) => (
                  <div
                    key={f.title}
                    className="bg-white rounded-2xl p-3 md:p-4 flex flex-col gap-2 shadow-sm hover:shadow-md transition-shadow cursor-default"
                    style={{
                      border: "1.5px solid transparent",
                      background: "linear-gradient(white, white) padding-box, linear-gradient(135deg, #a8edea, #fed6e3, #ffecd2, #a1c4fd) border-box",
                    }}
                  >
                    <img src={f.icon} alt={f.title} className="w-8 h-8 md:w-10 md:h-10 object-contain" />
                    <p className="text-xs font-semibold text-gray-700 leading-snug">{f.title}</p>
                    <p className="text-xs text-gray-400 leading-relaxed hidden md:block">{f.desc}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="w-full max-w-3xl pb-6 md:pb-8">
              <ChatInput
                value={message}
                onChange={setMessage}
                onSend={handleSend}
                onUploadClick={() => setActiveModal("upload")}
                disabled={isReplying}
              />
            </div>
          </div>
        )}

        {/* ── KONSELING ── */}
        {isKonseling && (
          <div className="relative z-10 flex flex-col flex-1 min-h-screen">
            <div className="flex-1 overflow-y-auto px-4 md:px-10 py-6 md:py-8 flex flex-col gap-5">
              {messages.map((msg) => (
                <ChatBubble key={msg.id} msg={msg} />
              ))}
              {isReplying && <TypingIndicator />}
              <div ref={chatEndRef} />
            </div>

            <div className="px-4 md:px-10 pb-6 md:pb-8 pt-2">
              <ChatInput
                value={message}
                onChange={setMessage}
                onSend={handleSend}
                onUploadClick={() => setActiveModal("upload")}
                disabled={isReplying}
              />
            </div>
          </div>
        )}
      </main>

      {/* ── MODALS ── */}
      {activeModal === "upload" && (
        <UploadKHSModal
          onClose={closeModal}
          onSuccess={(result) => {
            onKHSSuccess(result);
            closeModal();
            setActiveNav("konseling");
          }}
        />
      )}

      {activeModal === "rekomendasi" && (
        <RekomendasiModal
          onClose={closeModal}
          sessionId={sessionId}
          khsResult={khsResult}
        />
      )}

      {activeModal === "riwayat" && (
        <RiwayatModal
          onClose={closeModal}
          onMulaiChat={() => {
            closeModal();
            setActiveModal("upload");
          }}
          onLanjutChat={(sid: string) => {
            loadSession(sid);
            setActiveNav("konseling");
          }}
        />
      )}
    </div>
  );
}
