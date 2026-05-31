import { api } from "./api";

export interface UserData {
  nim: string;
  nama: string;
  email?: string;
  role: "mahasiswa" | "admin";
}

export interface RegisterRequest extends UserData {
  password: string;
}

// Token helpers (simpan JWT di localStorage)
const TOKEN_KEY = "chatbotfik_token";

export const tokenStorage = {
  get: (): string | null => localStorage.getItem(TOKEN_KEY),
  set: (token: string): void => localStorage.setItem(TOKEN_KEY, token),
  remove: (): void => localStorage.removeItem(TOKEN_KEY),
};

// AUTH SERVICE

export const authService = {
  // Register
  register: async (data: RegisterRequest) => {
    const response = await api.post("/register", data);
    return response.data;
  },

  // Login (simpan token ke localStorage)
  login: async (nim: string, pass: string) => {
    const response = await api.post("/login", { nim, password: pass });
    const { token, user } = response.data;
    if (token) tokenStorage.set(token);
    return { token, user };
  },

  // Get me (kirim token via Authorization header)
  getMe: async () => {
    const token = tokenStorage.get();
    const response = await api.get<UserData>("/me", {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    return response.data;
  },

  // Lupa password – kirim email reset
  forgotPassword: async (email: string) => {
    const response = await api.post("/forgot-password", { email });
    return response.data;
  },

  // Reset password dengan token dari email
  resetPassword: async (token: string, password: string) => {
    const response = await api.post("/reset-password", { token, password });
    return response.data;
  },

  // Logout
  logout: async () => {
    tokenStorage.remove();
    await api.post("/logout").catch(() => {});
  },
};
