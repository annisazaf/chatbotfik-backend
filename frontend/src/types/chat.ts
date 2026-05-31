export interface ChatMessage {
  id: number;
  role: "assistant" | "user";
  content: string;
}

export interface FeatureCard {
  icon: string;
  title: string;
  desc: string;
}

export interface KHSResult {
  session_id: string;
  khs_id: number;
  nama: string;
  nim: string;
  prodi: string;
  ipk: number;
  ips: number;
  sks_tempuh: number;
  sks_total: number;
  sks_sisa: number;
  mk_lulus: number;
  mk_belum_count: number;
  persen: number;
}

export interface RiwayatItem {
  session_id: string;
  title: string;
  preview: string;
  last_active: string;
  message_count: number;
}

export interface MataKuliahEligible {
  nama: string;
  sks: number;
  alasan: string;
}

export interface MataKuliahBelum {
  nama: string;
  alasan: string;
  keterangan: string;
}

export interface RekomendasiData {
  mk_eligible: MataKuliahEligible[];
  mk_belum: MataKuliahBelum[];
  strategi: string;
  karier: string;
}