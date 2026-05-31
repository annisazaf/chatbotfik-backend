import { useEffect, useState } from "react";
import { KHSResult, RekomendasiData, MataKuliahEligible, MataKuliahBelum } from "../../types/chat";
import { tokenStorage } from "../../services/authServices";

const API = import.meta.env.VITE_API_URL || "http://localhost:5000/api";

function authHeaders(): Record<string, string> {
  const token = tokenStorage.get();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

interface RekomendasiModalProps {
  onClose?: () => void;
  sessionId: string | null;
  khsResult: KHSResult | null;
}

type LoadState = "idle" | "loading" | "success" | "error";

interface FullRekomendasi extends RekomendasiData {
  nama?: string;
  nim?: string;
  prodi?: string;
  ipk?: number;
  ips?: number;
  sks_tempuh?: number;
}

function TableHeader({ cols }: { cols: string[] }) {
  return (
    <div className="grid px-3 py-2" style={{ gridTemplateColumns: `repeat(${cols.length}, 1fr)`, backgroundColor: "#307045" }}>
      {cols.map((h, i) => (
        <span key={h} className={`text-xs font-semibold text-white ${i === 0 ? "text-left" : "text-center"}`}>{h}</span>
      ))}
    </div>
  );
}

async function fetchRekomendasi(sessionId: string) {
  const r = await fetch(`${API}/chatbot/sessions/${sessionId}/rekomendasi`, {
    headers: authHeaders(),
  });
  const d = await r.json();
  if (!r.ok || d.error) throw new Error(d.error || `HTTP ${r.status}`);
  return d;
}

export default function RekomendasiModal({ onClose, sessionId, khsResult }: RekomendasiModalProps) {
  const [data, setData]           = useState<FullRekomendasi | null>(null);
  const [loadState, setLoadState] = useState<LoadState>("idle");
  const [errorMsg, setErrorMsg]   = useState<string>("");

  useEffect(() => {
    if (!sessionId) { setLoadState("idle"); return; }
    setLoadState("loading");
    setErrorMsg("");
    fetchRekomendasi(sessionId)
      .then((d) => { setData(d); setLoadState("success"); })
      .catch((e) => { setErrorMsg(e.message || "Terjadi kesalahan."); setLoadState("error"); });
  }, [sessionId]);

  const handleRetry = () => {
    if (!sessionId) return;
    setLoadState("loading");
    setErrorMsg("");
    fetchRekomendasi(sessionId)
      .then((d) => { setData(d); setLoadState("success"); })
      .catch((e) => { setErrorMsg(e.message); setLoadState("error"); });
  };

  const nama  = data?.nama  ?? khsResult?.nama  ?? "–";
  const nim   = data?.nim   ?? khsResult?.nim   ?? "–";
  const prodi = data?.prodi ?? khsResult?.prodi ?? "–";
  const ipk   = data?.ipk   ?? khsResult?.ipk   ?? "–";
  const ips   = data?.ips   ?? khsResult?.ips   ?? "–";
  const sks   = data?.sks_tempuh ?? khsResult?.sks_tempuh ?? "–";

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-end" onClick={onClose}>
      <div className="absolute inset-0 bg-black/20" />
      <div className="relative bg-white shadow-xl w-120 flex flex-col overflow-hidden h-full" onClick={(e) => e.stopPropagation()}>
        <div className="flex-1 overflow-y-auto px-5 pt-8 pb-8 flex flex-col gap-6">

          <h2 className="text-xl font-bold" style={{ color: "#307045" }}>Rekomendasi</h2>

          {!sessionId ? (
            <div className="rounded-xl bg-yellow-50 border border-yellow-100 px-4 py-3 text-sm text-yellow-600 text-center">
              Upload atau Pilih Riwayat Terlebih Dahulu
            </div>
          ) : (
            <>
              <div className="flex flex-col gap-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-full bg-gray-200 flex-shrink-0 flex items-center justify-center text-gray-500 font-semibold text-lg">
                    {nama.charAt(0)}
                  </div>
                  <div className="flex flex-col gap-0.5">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-bold text-gray-800">{nama}</span>
                      <span className="text-xs px-2 py-0.5 rounded-full text-white font-medium" style={{ backgroundColor: "#307045" }}>{prodi}</span>
                    </div>
                    <span className="text-xs text-gray-400">{nim}</span>
                  </div>
                </div>
                <div className="grid grid-cols-3 divide-x divide-gray-100 border border-gray-100 rounded-2xl">
                  {[{ label: "SKS LULUS", value: sks }, { label: "IPK", value: ipk }, { label: "IPS", value: ips }].map((s) => (
                    <div key={s.label} className="flex flex-col items-center py-3 gap-1">
                      <span className="text-xs text-gray-400 font-medium tracking-wide">{s.label}</span>
                      <span className="text-base font-bold text-gray-800">{s.value}</span>
                    </div>
                  ))}
                </div>
              </div>

              {loadState === "loading" && (
                <div className="flex flex-col items-center gap-3 py-10">
                  <div className="w-8 h-8 rounded-full border-2 border-t-transparent animate-spin" style={{ borderColor: "#307045", borderTopColor: "transparent" }} />
                  <p className="text-sm text-gray-400">Memuat rekomendasi AI...</p>
                </div>
              )}

              {loadState === "error" && (
                <div className="flex flex-col gap-2">
                  <div className="rounded-xl bg-red-50 border border-red-100 px-4 py-3 text-sm text-red-500 text-center">
                    {errorMsg || "Gagal memuat rekomendasi."}
                  </div>
                  <button onClick={handleRetry} className="text-xs text-center py-2 rounded-xl border border-gray-200 text-gray-500 hover:bg-gray-50 transition-colors">
                    Coba lagi
                  </button>
                </div>
              )}

              {loadState === "success" && data && (
                <>
                  <div className="flex flex-col gap-2">
                    <h3 className="text-sm font-bold text-gray-800">Mata Kuliah Eligible</h3>
                    <div className="rounded-xl overflow-hidden border border-gray-100">
                      <TableHeader cols={["MATA KULIAH", "SKS", "ALASAN"]} />
                      {data.mk_eligible.length === 0 ? (
                        <p className="text-xs text-gray-400 text-center py-4">Tidak ada data.</p>
                      ) : data.mk_eligible.map((row: MataKuliahEligible, i: number) => (
                        <div key={i} className={`grid grid-cols-3 px-3 py-2 ${i % 2 === 0 ? "bg-white" : "bg-green-50"}`}>
                          <span className="text-xs text-gray-700">{row.nama}</span>
                          <span className="text-xs font-semibold text-center" style={{ color: "#307045" }}>{row.sks}</span>
                          <span className="text-xs text-gray-500 text-center">{row.alasan}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="flex flex-col gap-2">
                    <h3 className="text-sm font-bold text-gray-800">Mata Kuliah Belum Dapat Diambil</h3>
                    <div className="rounded-xl overflow-hidden border border-gray-100">
                      <TableHeader cols={["MATA KULIAH", "ALASAN", "KETERANGAN"]} />
                      {data.mk_belum.length === 0 ? (
                        <p className="text-xs text-gray-400 text-center py-4">Tidak ada data.</p>
                      ) : data.mk_belum.map((row: MataKuliahBelum, i: number) => (
                        <div key={i} className={`grid grid-cols-3 px-3 py-2 ${i % 2 === 0 ? "bg-white" : "bg-green-50"}`}>
                          <span className="text-xs text-gray-700">{row.nama}</span>
                          <span className="text-xs text-gray-500 text-center">{row.alasan}</span>
                          <span className="text-xs text-gray-500 text-center">{row.keterangan}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="flex flex-col gap-1">
                    <h3 className="text-sm font-bold text-gray-800">Rekomendasi Strategi Akademik</h3>
                    <p className="text-xs text-gray-500 leading-relaxed">{data.strategi}</p>
                  </div>

                  <div className="flex flex-col gap-1">
                    <h3 className="text-sm font-bold text-gray-800">Rekomendasi Karier</h3>
                    <p className="text-xs text-gray-500 leading-relaxed">{data.karier}</p>
                  </div>
                </>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
