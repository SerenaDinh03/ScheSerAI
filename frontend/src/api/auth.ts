import { apiFetch, ensureCsrfCookie } from "./client";

export interface AuthUser {
  username: string;
  name: string;
  email: string;
}

export async function fetchCurrentUser(): Promise<AuthUser | null> {
  try {
    return await apiFetch<AuthUser>("/api/auth/me/");
  } catch {
    return null;
  }
}

export async function login(username: string, password: string): Promise<AuthUser> {
  await ensureCsrfCookie();
  return apiFetch<AuthUser>("/api/auth/login/", { method: "POST", body: { username, password } });
}

export async function logout(): Promise<void> {
  await apiFetch("/api/auth/logout/", { method: "POST" });
}
