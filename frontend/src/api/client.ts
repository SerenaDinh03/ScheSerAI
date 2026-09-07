export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

const SAFE_METHODS = new Set(["GET", "HEAD", "OPTIONS"]);

export class ApiError extends Error {
  status: number;
  body: unknown;

  constructor(status: number, body: unknown, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

function readCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

type Params = Record<string, string | number | boolean | undefined>;

interface RequestOptions {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  body?: unknown;
  params?: Params;
}

/** Fetch wrapper dùng chung: gắn cookie session, kèm CSRF token cho request
 * không an toàn (Django SessionAuthentication.enforce_csrf yêu cầu điều này
 * cho mọi request có user đã đăng nhập - xem apps/teacher/views.py CsrfView). */
export async function apiFetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, params } = options;

  const url = new URL(path, API_BASE_URL);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== "") url.searchParams.set(key, String(value));
    }
  }

  const headers: Record<string, string> = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (!SAFE_METHODS.has(method)) {
    const csrftoken = readCookie("csrftoken");
    if (csrftoken) headers["X-CSRFToken"] = csrftoken;
  }

  const res = await fetch(url.toString(), {
    method,
    headers,
    credentials: "include",
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (res.status === 204) return undefined as T;

  const contentType = res.headers.get("content-type") ?? "";
  const data = contentType.includes("application/json") ? await res.json() : await res.text();

  if (!res.ok) {
    const detail =
      data && typeof data === "object" && "detail" in (data as Record<string, unknown>)
        ? (data as Record<string, unknown>).detail
        : undefined;
    const message = typeof detail === "string" ? detail : `Yêu cầu thất bại (${res.status})`;
    throw new ApiError(res.status, data, message);
  }

  return data as T;
}

export async function ensureCsrfCookie(): Promise<void> {
  await apiFetch("/api/auth/csrf/");
}
