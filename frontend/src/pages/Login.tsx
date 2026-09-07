import { useState } from "react";
import type { FormEvent } from "react";
import styles from "./Login.module.css";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { useAuth } from "../context/AuthContext";

export function Login() {
  const { login, error } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      await login(username, password);
    } catch {
      // lỗi đã được AuthContext lưu lại, hiển thị bên dưới
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className={styles.page}>
      <Card className={styles.card}>
        <div className={styles.brandMark}>🌸</div>
        <div>
          <h1 className={styles.title}>ScheSerAI</h1>
          <p className={styles.subtitle}>Đăng nhập để xem lịch dạy, học viên và học phí.</p>
        </div>

        <form className={styles.form} onSubmit={handleSubmit}>
          {error && <div className={styles.error}>{error}</div>}
          <div>
            <label className={styles.label} htmlFor="username">
              Tên đăng nhập
            </label>
            <input
              id="username"
              className={styles.input}
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              required
            />
          </div>
          <div>
            <label className={styles.label} htmlFor="password">
              Mật khẩu
            </label>
            <input
              id="password"
              type="password"
              className={styles.input}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </div>
          <Button type="submit" variant="primary" disabled={submitting}>
            {submitting ? "Đang đăng nhập..." : "Đăng nhập"}
          </Button>
        </form>
      </Card>
    </div>
  );
}
