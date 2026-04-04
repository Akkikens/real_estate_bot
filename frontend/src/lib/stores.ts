/**
 * Zustand stores for client-side state.
 *
 * Auth is fully managed by Clerk — no local auth store needed.
 * This file only contains UI state management.
 */

import { create } from "zustand";

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
