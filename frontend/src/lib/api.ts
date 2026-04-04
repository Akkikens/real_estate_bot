/**
 * API client for the HouseMatch FastAPI backend.
 *
 * Handles:
 * - Base URL configuration
 * - Auth token injection via Authorization header
 * - Automatic token refresh on 401
 * - Typed fetch wrapper
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Token storage (client-side only) ─────────────────────────────────────────

const TOKEN_KEY = "hm_access_token";
const REFRESH_KEY = "hm_refresh_token";

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(REFRESH_KEY);
}

export function setTokens(access: string, refresh: string) {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
}

export function clearTokens() {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

// ── API error class ──────────────────────────────────────────────────────────

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

// ── Core fetch wrapper ───────────────────────────────────────────────────────

type FetchOptions = {
  method?: string;
  body?: unknown;
  headers?: Record<string, string>;
  auth?: boolean; // default true — set false for public endpoints
};

async function refreshAccessToken(): Promise<string | null> {
  const refresh = getRefreshToken();
  if (!refresh) return null;

  try {
    const res = await fetch(`${API_BASE}/api/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refresh }),
    });

    if (!res.ok) {
      clearTokens();
      return null;
    }

    const data = await res.json();
    setTokens(data.access_token, data.refresh_token);
    return data.access_token;
  } catch {
    clearTokens();
    return null;
  }
}

export async function apiFetch<T>(
  path: string,
  options: FetchOptions = {}
): Promise<T> {
  const { method = "GET", body, headers = {}, auth = true } = options;

  const reqHeaders: Record<string, string> = {
    "Content-Type": "application/json",
    ...headers,
  };

  if (auth) {
    const token = getAccessToken();
    if (token) {
      reqHeaders["Authorization"] = `Bearer ${token}`;
    }
  }

  const url = path.startsWith("http") ? path : `${API_BASE}${path}`;

  let res = await fetch(url, {
    method,
    headers: reqHeaders,
    body: body ? JSON.stringify(body) : undefined,
  });

  // Auto-refresh on 401
  if (res.status === 401 && auth) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      reqHeaders["Authorization"] = `Bearer ${newToken}`;
      res = await fetch(url, {
        method,
        headers: reqHeaders,
        body: body ? JSON.stringify(body) : undefined,
      });
    }
  }

  if (!res.ok) {
    let detail = `Request failed with status ${res.status}`;
    try {
      const err = await res.json();
      detail = err.detail || detail;
    } catch {
      // ignore parse errors
    }
    throw new ApiError(res.status, detail);
  }

  // Handle 204 No Content
  if (res.status === 204) return undefined as T;

  return res.json();
}

// ── Convenience wrappers ─────────────────────────────────────────────────────

export const api = {
  get: <T>(path: string, opts?: Omit<FetchOptions, "method">) =>
    apiFetch<T>(path, { ...opts, method: "GET" }),

  post: <T>(path: string, body?: unknown, opts?: Omit<FetchOptions, "method" | "body">) =>
    apiFetch<T>(path, { ...opts, method: "POST", body }),

  put: <T>(path: string, body?: unknown, opts?: Omit<FetchOptions, "method" | "body">) =>
    apiFetch<T>(path, { ...opts, method: "PUT", body }),

  delete: <T>(path: string, opts?: Omit<FetchOptions, "method">) =>
    apiFetch<T>(path, { ...opts, method: "DELETE" }),
};
