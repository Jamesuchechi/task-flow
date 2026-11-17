import type { Token } from "../types/api";

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const ACCESS_TOKEN_KEY = "taskflow_access_token";
const REFRESH_TOKEN_KEY = "taskflow_refresh_token";

export class ApiError extends Error {
  status: number;
  code: string;

  constructor(message: string, status: number, code = "API_ERROR") {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setTokens(accessToken: string, refreshToken?: string | null): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  if (refreshToken) {
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  }
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

async function parseErrorResponse(res: Response): Promise<ApiError> {
  let message = `Request failed with status ${res.status}`;
  let code = `HTTP_${res.status}`;

  try {
    const body = await res.json();
    if (body?.error?.message) {
      message = body.error.message;
      code = body.error.code || code;
    } else if (typeof body?.detail === "string") {
      message = body.detail;
    } else if (Array.isArray(body?.detail) && body.detail.length > 0) {
      message = body.detail
        .map((err: { loc?: unknown[]; msg?: string }) => {
          const field = Array.isArray(err.loc) ? err.loc.slice(1).join(".") : "";
          return field ? `${field}: ${err.msg}` : err.msg;
        })
        .join("; ");
      code = "VALIDATION_ERROR";
    }
  } catch {
    // Response had no JSON body
  }

  if (res.status === 429 && code === "HTTP_429") {
    code = "RATE_LIMIT_EXCEEDED";
  }

  return new ApiError(message, res.status, code);
}

let refreshPromise: Promise<boolean> | null = null;

async function tryRefreshTokens(): Promise<boolean> {
  if (refreshPromise) {
    return refreshPromise;
  }

  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    return false;
  }

  refreshPromise = (async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      if (!res.ok) {
        clearTokens();
        return false;
      }
      const data: Token = await res.json();
      setTokens(data.access_token, data.refresh_token);
      return true;
    } catch {
      clearTokens();
      return false;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

export interface RequestOptions extends RequestInit {
  skipAuth?: boolean;
}

export async function apiFetchRaw(
  path: string,
  options: RequestOptions = {}
): Promise<Response> {
  const { skipAuth = false, headers: initHeaders, ...rest } = options;
  const headers = new Headers(initHeaders);

  if (!skipAuth) {
    const token = getAccessToken();
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
  }

  let res = await fetch(`${API_BASE_URL}${path}`, {
    ...rest,
    headers,
  });

  if (res.status === 401 && !skipAuth) {
    const refreshed = await tryRefreshTokens();
    if (refreshed) {
      const newToken = getAccessToken();
      if (newToken) {
        headers.set("Authorization", `Bearer ${newToken}`);
      }
      res = await fetch(`${API_BASE_URL}${path}`, {
        ...rest,
        headers,
      });
    }
  }

  if (!res.ok) {
    throw await parseErrorResponse(res);
  }

  return res;
}

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  const headers = new Headers(options.headers);
  if (
    options.body &&
    !(options.body instanceof FormData) &&
    !(options.body instanceof URLSearchParams) &&
    !headers.has("Content-Type")
  ) {
    headers.set("Content-Type", "application/json");
  }

  const res = await apiFetchRaw(path, { ...options, headers });
  if (res.status === 204) {
    return undefined as T;
  }
  return (await res.json()) as T;
}

export async function downloadProtectedFile(
  path: string,
  fallbackFilename: string
): Promise<void> {
  const res = await apiFetchRaw(path, { method: "GET" });
  const blob = await res.blob();

  let filename = fallbackFilename;
  const disposition = res.headers.get("Content-Disposition");
  if (disposition) {
    const match = disposition.match(/filename\*?=(?:UTF-8'')?["']?([^"';]+)["']?/i);
    if (match?.[1]) {
      filename = decodeURIComponent(match[1]);
    }
  }

  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}
