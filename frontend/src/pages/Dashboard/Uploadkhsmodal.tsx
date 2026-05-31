import { useState, useRef, useEffect } from "react";
import { KHSResult } from "../../types/chat";
import { tokenStorage } from "../../services/authServices";

const API = import.meta.env.VITE_API_URL || "http://localhost:5000/api";

// Header JWT
function authHeaders(extra: Record<string, string> = {}): Record<string, string> {
  const token = tokenStorage.get();
  return {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...extra,
  };
}

const PaperclipIcon = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
  </svg>
);

const CheckIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#307045" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="20 6 9 17 4 12"/>
  </svg>
);

interface UploadKHSModalProps {
  onClose?: () => void;
  onSuccess?: (result: KHSResult) => void;
}

type UploadState = "idle" | "loading" | "success" | "error";

interface LatestKHS {
  has_khs: boolean;
  nama?: string;
  ipk?: number;
  ips?: number;
  sks_tempuh?: number;
  sks_total?: number;
  persen?: number;
  mk_lulus?: number;
  upload_time?: string;
}

export default function UploadKHSModal({ onClose, onSuccess }: UploadKHSModalProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile]   = useState<File | null>(null);
  const [uploadState, setUploadState]     = useState<UploadState>("idle");
  const [errorMessage, setErrorMessage]   = useState<string>("");
  const [result, setResult]               = useState<KHSResult | null>(null);
  const [latestKHS, setLatestKHS]         = useState<LatestKHS | null>(null);
  const [loadingLatest, setLoadingLatest] = useState(true);

  // Ambil data KHS terakhir saat modal dibuka
  useEffect(() => {
    const fetchLatest = async () => {
      try {
        const res = await fetch(`${API}/chatbot/khs/latest`, {
          headers: authHeaders(),
        });
        const data = await res.json();
        setLatestKHS(data);
      } catch {
        setLatestKHS({ has_khs: false });
      } finally {
        setLoadingLatest(false);
      }
    };
    fetchLatest();
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setSelectedFile(file);
    setUploadState("idle");
    setErrorMessage("");
    setResult(null);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    setUploadState("loading");
    setErrorMessage("");

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const res = await fetch(`${API}/chatbot/upload`, {
        method: "POST",
        headers: authHeaders(), // Note: jangan tambah Content-Type untuk FormData
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Gagal mengupload KHS.");
      setResult(data);
      setUploadState("success");
      onSuccess?.(data);
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : "Terjadi kesalahan.");
      setUploadState("error");
    }
  };

  const isLoading = uploadState === "loading";
  const isSuccess = uploadState === "success";

  const formatDate = (iso?: string) => {
    if (!iso) return "-";
    return new Date(iso).toLocaleDateString("id-ID", {
      day: "numeric", month: "short", year: "numeric",
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-end" onClick={onClose}>
      <div className="absolute inset-0 bg-black/20" />
      <div
        className="relative bg-white shadow-xl w-72 flex flex-col overflow-hidden h-full"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex-1 overflow-y-auto px-5 pt-8 pb-4 flex flex-col gap-5">

          {/* Title */}
          <div>
            <h2 className="text-xl font-bold leading-snug" style={{ color: "#307045" }}>
              Upload Kartu Hasil Studi
            </h2>
            <p className="text-sm text-gray-500 mt-2">
              Unggah KHS terbaru untuk dianalisis oleh sistem.
            </p>
          </div>

          {/* Preview area */}
          <div
            className="rounded-2xl border-2 border-dashed border-gray-200 bg-gray-50 flex items-center justify-center overflow-hidden cursor-pointer"
            style={{ minHeight: 160 }}
            onClick={() => !isLoading && !isSuccess && fileInputRef.current?.click()}
          >
            {isSuccess ? (
              <div className="flex flex-col items-center gap-2 py-8 px-4 text-center">
                <div className="w-12 h-12 rounded-full flex items-center justify-center" style={{ backgroundColor: "#e8f5ed" }}>
                  <CheckIcon />
                </div>
                <p className="text-sm font-semibold text-gray-700">KHS berhasil diproses!</p>
                <p className="text-xs text-gray-400">{selectedFile?.name}</p>
              </div>
            ) : isLoading ? (
              <div className="flex flex-col items-center gap-3 py-8 px-4 text-center">
                <div className="w-8 h-8 rounded-full border-2 border-t-transparent animate-spin"
                  style={{ borderColor: "#307045", borderTopColor: "transparent" }} />
                <p className="text-sm text-gray-500">Memproses KHS...</p>
              </div>
            ) : selectedFile ? (
              <div className="flex flex-col items-center gap-2 py-8 px-4 text-center">
                <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#307045" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                </svg>
                <p className="text-sm font-semibold text-gray-700">{selectedFile.name}</p>
                <p className="text-xs text-gray-400">{(selectedFile.size / 1024).toFixed(1)} KB</p>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-2 py-8 px-4 text-center">
                <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#ccc" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="3" y="3" width="18" height="18" rx="2"/>
                  <path d="M3 9h18M9 21V9"/>
                </svg>
                <p className="text-xs text-gray-400">Klik untuk pilih file KHS</p>
              </div>
            )}
          </div>

          {/* Error */}
          {uploadState === "error" && (
            <div className="rounded-xl bg-red-50 border border-red-100 px-4 py-3 text-sm text-red-600">
              ⚠ {errorMessage}
            </div>
          )}

          {/* Pilih file button */}
          {!isLoading && !isSuccess && (
            <button
              onClick={() => fileInputRef.current?.click()}
              className="flex items-center justify-center gap-2 w-full py-2.5 rounded-full border border-gray-300 text-sm font-medium text-gray-600 hover:bg-gray-50 transition-colors"
            >
              <PaperclipIcon />
              {selectedFile ? "Perbarui KHS" : "Pilih File KHS"}
            </button>
          )}

          <input ref={fileInputRef} type="file" accept=".pdf" className="hidden" onChange={handleFileChange} />

          {/* Syarat */}
          {!isSuccess && (
            <div>
              <p className="text-xs font-semibold text-gray-700 mb-1">Syarat Upload KHS ▾</p>
              <ul className="text-xs text-gray-500 flex flex-col gap-1 pl-1">
                <li>• File harus dalam format PDF (.pdf)</li>
                <li>• PDF asli dari SIAKAD, bukan hasil scan</li>
                <li>• File dapat dibaca (tidak blur atau rusak)</li>
              </ul>
            </div>
          )}

          {/* KHS Terakhir */}
          {!isSuccess && !loadingLatest && latestKHS?.has_khs && (
            <div className="rounded-2xl border border-gray-100 bg-gray-50 px-4 py-3 flex flex-col gap-2.5">
              <div className="flex items-center justify-between">
                <p className="text-xs font-semibold text-gray-700">KHS Terakhir</p>
                <span className="text-xs text-gray-400">{formatDate(latestKHS.upload_time)}</span>
              </div>
              <div className="grid grid-cols-3 divide-x divide-gray-200 border border-gray-100 rounded-xl bg-white">
                {[
                  { label: "IPK", value: latestKHS.ipk },
                  { label: "IPS", value: latestKHS.ips },
                  { label: "SKS", value: `${latestKHS.sks_tempuh}/${latestKHS.sks_total}` },
                ].map((s) => (
                  <div key={s.label} className="flex flex-col items-center py-2.5 gap-0.5">
                    <span className="text-xs text-gray-400">{s.label}</span>
                    <span className="text-sm font-bold text-gray-800">{s.value}</span>
                  </div>
                ))}
              </div>
              <div>
                <div className="flex justify-between text-xs text-gray-400 mb-1">
                  <span>Progres Studi</span>
                  <span style={{ color: "#307045" }}>{latestKHS.persen}%</span>
                </div>
                <div className="h-1.5 rounded-full bg-gray-200 overflow-hidden">
                  <div className="h-full rounded-full" style={{ width: `${latestKHS.persen}%`, backgroundColor: "#307045" }} />
                </div>
              </div>
              <p className="text-xs text-gray-400 text-center">Upload KHS baru untuk memperbarui data ini</p>
            </div>
          )}

          {/* Loading latest KHS */}
          {!isSuccess && loadingLatest && (
            <div className="rounded-2xl border border-gray-100 bg-gray-50 px-4 py-4 flex items-center justify-center gap-2">
              <div className="w-4 h-4 rounded-full border-2 animate-spin"
                style={{ borderColor: "#307045", borderTopColor: "transparent" }} />
              <span className="text-xs text-gray-400">Memuat data KHS...</span>
            </div>
          )}

          <div className="h-px bg-gray-100" />

          {/* Ringkasan setelah sukses */}
          {isSuccess && result && (
            <div className="flex flex-col gap-3">
              <p className="text-sm font-bold text-gray-800">Ringkasan KHS</p>
              <div className="flex flex-col gap-1.5">
                {[
                  { label: "Nama",          value: result.nama },
                  { label: "NIM",           value: result.nim },
                  { label: "Program Studi", value: result.prodi },
                ].map(({ label, value }) => (
                  <div key={label} className="flex justify-between items-start gap-2">
                    <span className="text-xs text-gray-400 flex-shrink-0">{label}</span>
                    <span className="text-xs font-medium text-gray-700 text-right">{value}</span>
                  </div>
                ))}
              </div>
              <div className="grid grid-cols-3 divide-x divide-gray-100 border border-gray-100 rounded-2xl">
                {[
                  { label: "IPK", value: result.ipk },
                  { label: "IPS", value: result.ips },
                  { label: "SKS", value: `${result.sks_tempuh}/${result.sks_total}` },
                ].map((s) => (
                  <div key={s.label} className="flex flex-col items-center py-3 gap-0.5">
                    <span className="text-xs text-gray-400 font-medium tracking-wide">{s.label}</span>
                    <span className="text-sm font-bold text-gray-800">{s.value}</span>
                  </div>
                ))}
              </div>
              <div>
                <div className="flex justify-between text-xs text-gray-400 mb-1">
                  <span>Progres Studi</span>
                  <span style={{ color: "#307045" }}>{result.persen}%</span>
                </div>
                <div className="h-2 rounded-full bg-gray-100 overflow-hidden">
                  <div className="h-full rounded-full transition-all duration-700"
                    style={{ width: `${result.persen}%`, backgroundColor: "#307045" }} />
                </div>
              </div>
              <div className="flex gap-2">
                <div className="flex-1 rounded-xl bg-green-50 px-3 py-2.5 text-center">
                  <p className="text-lg font-bold" style={{ color: "#307045" }}>{result.mk_lulus}</p>
                  <p className="text-xs text-gray-500">MK Lulus</p>
                </div>
                <div className="flex-1 rounded-xl bg-red-50 px-3 py-2.5 text-center">
                  <p className="text-lg font-bold text-red-400">{result.mk_belum_count}</p>
                  <p className="text-xs text-gray-500">MK Belum</p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-5 pb-6 pt-3">
          {isSuccess ? (
            <button onClick={onClose} className="w-full py-3.5 rounded-2xl text-white text-sm font-semibold" style={{ backgroundColor: "#307045" }}>
              Mulai Chat →
            </button>
          ) : (
            <button onClick={handleUpload} disabled={!selectedFile || isLoading}
              className="w-full py-3.5 rounded-2xl text-white text-sm font-semibold disabled:opacity-40 disabled:cursor-not-allowed"
              style={{ backgroundColor: "#307045" }}>
              {isLoading ? "Memproses..." : "Upload & Proses"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
