/**
 * API client for the HouseMatch FastAPI backend.
 *
 * Auth tokens are injected via Clerk's getToken() — see useApiAuth hook.
 * No localStorage token management; Clerk handles sessions via httpOnly cookies.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Clerk token getter (set by useApiAuth hook) ──────────────────────────────

let _getToken: (() => Promise<string | null>) | null = null;

export function setTokenGetter(getter: () => Promise<string | null>) {
  _getToken = getter;
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

export async function apiFetch<T>(
  path: string,
  options: FetchOptions = {}
): Promise<T> {
  const { method = "GET", body, headers = {}, auth = true } = options;

  const reqHeaders: Record<string, string> = {
    "Content-Type": "application/json",
    ...headers,
  };

  // Inject Clerk session token for authenticated requests
  if (auth && _getToken) {
    try {
      const token = await _getToken();
      if (token) {
        reqHeaders["Authorization"] = `Bearer ${token}`;
      }
    } catch {
      // Token fetch failed — proceed without auth header
      // Clerk will handle session refresh automatically
    }
  }

  const url = path.startsWith("http") ? path : `${API_BASE}${path}`;

  const res = await fetch(url, {
    method,
    headers: reqHeaders,
    body: body ? JSON.stringify(body) : undefined,
  });

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
