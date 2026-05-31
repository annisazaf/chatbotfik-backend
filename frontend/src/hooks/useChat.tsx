// src/hooks/useChat.tsx

import { useState } from "react";
import { ChatMessage, KHSResult } from "../types/chat";
import { tokenStorage } from "../services/authServices";

const API = import.meta.env.VITE_API_URL || "http://localhost:5000/api";

const INITIAL_MESSAGES: ChatMessage[] = [
  {
    id: 1,
    role: "assistant",
    content: `Halo! 👋\nAku FIKA, Asisten Konseling Akademik dan Karier Mahasiswa FIK UPN "Veteran" Jakarta.\n\nSebelum mulai, pastikan kamu sudah mengunggah KHS terbaru agar analisisku lebih akurat. Upload di menu Upload KHS ya 😊`,
  },
];

// Header JWT untuk setiap request
function authHeaders(extra: Record<string, string> = {}): Record<string, string> {
  const token = tokenStorage.get();
  return {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...extra,
  };
}

// Pesan error yang ramah berdasarkan jenis error
function parseErrorMessage(err: unknown): string {
  if (err instanceof Error) {
    const msg = err.message.toLowerCase();
    if (msg.includes("failed to fetch") || msg.includes("network"))
      return "Tidak dapat terhubung ke server. Pastikan backend sudah berjalan ya 🙏";
    if (msg.includes("timeout") || msg.includes("timed out"))
      return "Respons AI terlalu lama. Coba kirim pesan lagi dalam beberapa saat 🕐";
    if (msg.includes("502") || msg.includes("503"))
      return "Server sedang sibuk. Coba beberapa saat lagi ya 🔄";
    return err.message;
  }
  return "Terjadi kesalahan. Coba lagi.";
}

// Fetch dengan timeout agar tidak menggantung selamanya
async function fetchWithTimeout(url: string, options: RequestInit, ms = 70000): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), ms);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } catch (e) {
    if ((e as Error).name === "AbortError")
      throw new Error("Respons AI terlalu lama (timeout 70 detik). Coba kirim ulang pesan.");
    throw e;
  } finally {
    clearTimeout(timer);
  }
}

export function useChat() {
  const [messages, setMessages]     = useState<ChatMessage[]>(INITIAL_MESSAGES);
  const [sessionId, setSessionId]   = useState<string | null>(null);
  const [khsResult, setKhsResult]   = useState<KHSResult | null>(null);
  const [isReplying, setIsReplying] = useState(false);

  // ── Setelah upload KHS sukses ──
  const onKHSSuccess = (result: KHSResult) => {
    setSessionId(result.session_id);
    setKhsResult(result);
    setMessages([
      INITIAL_MESSAGES[0],
      {
        id: Date.now(),
        role: "assistant",
        content: `KHS kamu berhasil diproses! 🎉\n\nBerikut ringkasannya:\n• Nama: ${result.nama}\n• IPK: ${result.ipk} | IPS: ${result.ips}\n• SKS Lulus: ${result.sks_tempuh} / ${result.sks_total} (${result.persen}%)\n\nAda yang ingin kamu diskusikan tentang studi atau kariermu?`,
      },
    ]);
  };

  // ── Lanjut sesi lama dari riwayat ──
  const loadSession = async (sid: string) => {
    try {
      const res = await fetchWithTimeout(
        `${API}/chatbot/sessions/${sid}`,
        { headers: authHeaders() }
      );
      const data = await res.json();
      if (!res.ok) throw new Error(data.error);

      setSessionId(sid);
      const loaded: ChatMessage[] = (data.messages ?? []).map(
        (m: { id: number; role: "user" | "assistant"; content: string }) => ({
          id: m.id, role: m.role, content: m.content,
        })
      );
      setMessages(loaded.length > 0 ? loaded : INITIAL_MESSAGES);

      if (data.khs_upload_id) {
        const khsRes  = await fetchWithTimeout(
          `${API}/chatbot/sessions/${sid}/khs`,
          { headers: authHeaders() }
        );
        const khsData = await khsRes.json();
        if (khsRes.ok) setKhsResult(khsData as KHSResult);
      }
    } catch {
      // Gagal load sesi — biarkan state apa adanya
    }
  };

  // ── Kirim pesan ──
  const sendMessage = async (text: string) => {
    if (!text.trim() || isReplying) return;

    setMessages(prev => [...prev, { id: Date.now(), role: "user", content: text.trim() }]);
    setIsReplying(true);

    try {
      if (!sessionId) {
        setTimeout(() => {
          setMessages(prev => [...prev, {
            id: Date.now() + 1,
            role: "assistant",
            content: "Silakan upload KHS terlebih dahulu agar aku bisa memberikan analisis yang akurat ya! 😊",
          }]);
          setIsReplying(false);
        }, 600);
        return;
      }

      const res = await fetchWithTimeout(
        `${API}/chatbot/chat`,
        {
          method: "POST",
          headers: authHeaders({ "Content-Type": "application/json" }),
          body: JSON.stringify({ session_id: sessionId, pesan: text.trim() }),
        },
        70000
      );

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Gagal mendapat respons.");

      setMessages(prev => [...prev, { id: Date.now() + 1, role: "assistant", content: data.jawaban }]);

    } catch (err) {
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: "assistant",
        content: `⚠️ ${parseErrorMessage(err)}`,
      }]);
    } finally {
      setIsReplying(false);
    }
  };

  return { messages, sessionId, khsResult, isReplying, sendMessage, onKHSSuccess, loadSession };
}
