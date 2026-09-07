import { createContext, useCallback, useContext, useEffect, useState } from "react";
import type { PropsWithChildren } from "react";
import { ensureCsrfCookie } from "../api/client";
import { fetchCurrentUser, login as apiLogin, logout as apiLogout } from "../api/auth";
import type { AuthUser } from "../api/auth";

type Status = "loading" | "authenticated" | "anonymous";

interface AuthContextValue {
  user: AuthUser | null;
  status: Status;
  error: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: PropsWithChildren) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [status, setStatus] = useState<Status>("loading");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      await ensureCsrfCookie().catch(() => undefined);
      const current = await fetchCurrentUser();
      setUser(current);
      setStatus(current ? "authenticated" : "anonymous");
    })();
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    setError(null);
    try {
      await apiLogin(username, password);
      // apiLogin() chỉ trả username - gọi lại /auth/me/ để lấy đủ hồ sơ (tên, email).
      const current = await fetchCurrentUser();
      setUser(current);
      setStatus("authenticated");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Đăng nhập thất bại.");
      throw err;
    }
  }, []);

  const logout = useCallback(async () => {
    await apiLogout().catch(() => undefined);
    setUser(null);
    setStatus("anonymous");
  }, []);

  return (
    <AuthContext.Provider value={{ user, status, error, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth phải dùng bên trong AuthProvider");
  return ctx;
}
