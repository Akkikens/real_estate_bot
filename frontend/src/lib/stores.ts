/**
 * Zustand stores for client-side state.
 *
 * - useAuthStore: user session, login/logout, token management
 * - useUIStore: sidebar, view mode, filter sheet, command palette
 */

import { create } from "zustand";
import type { User, UserPreferences } from "./types";
import { api, setTokens, clearTokens, getAccessToken } from "./api";
import type { TokenResponse, UserProfile } from "./types";

// ── Auth Store ───────────────────────────────────────────────────────────────

interface AuthState {
  user: User | null;
  preferences: UserPreferences | null;
  isLoading: boolean;
  isAuthenticated: boolean;

  // Actions
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, name?: string, phone?: string, marketId?: string) => Promise<void>;
  logout: () => void;
  loadUser: () => Promise<void>;
  updatePreferences: (prefs: Partial<UserPreferences>) => Promise<void>;
  setUser: (user: User) => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  preferences: null,
  isLoading: true,
  isAuthenticated: false,

  login: async (email, password) => {
    const data = await api.post<TokenResponse>("/api/auth/login", { email, password }, { auth: false });
    setTokens(data.access_token, data.refresh_token);
    set({ user: data.user, isAuthenticated: true });
    // Load preferences in background
    get().loadUser();
  },

  signup: async (email, password, name, phone, marketId) => {
    const data = await api.post<TokenResponse>("/api/auth/signup", {
      email, password, name, phone, market_id: marketId || "bay_area",
    }, { auth: false });
    setTokens(data.access_token, data.refresh_token);
    set({ user: data.user, isAuthenticated: true });
  },

  logout: () => {
    clearTokens();
    set({ user: null, preferences: null, isAuthenticated: false });
  },

  loadUser: async () => {
    const token = getAccessToken();
    if (!token) {
      set({ isLoading: false, isAuthenticated: false });
      return;
    }
    try {
      const profile = await api.get<UserProfile>("/api/auth/profile");
      set({
        user: profile.user,
        preferences: profile.preferences,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch {
      set({ isLoading: false, isAuthenticated: false });
      clearTokens();
    }
  },

  updatePreferences: async (prefs) => {
    const updated = await api.put<UserPreferences>("/api/auth/profile/preferences", prefs);
    set({ preferences: updated });
  },

  setUser: (user) => set({ user }),
}));

// ── UI Store ─────────────────────────────────────────────────────────────────

interface UIState {
  sidebarOpen: boolean;
  viewMode: "grid" | "list" | "map";
  filterSheetOpen: boolean;
  commandPaletteOpen: boolean;

  setSidebarOpen: (open: boolean) => void;
  setViewMode: (mode: "grid" | "list" | "map") => void;
  setFilterSheetOpen: (open: boolean) => void;
  setCommandPaletteOpen: (open: boolean) => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: false,
  viewMode: "grid",
  filterSheetOpen: false,
  commandPaletteOpen: false,

  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  setViewMode: (mode) => set({ viewMode: mode }),
  setFilterSheetOpen: (open) => set({ filterSheetOpen: open }),
  setCommandPaletteOpen: (open) => set({ commandPaletteOpen: open }),
}));
