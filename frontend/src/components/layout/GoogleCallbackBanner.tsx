import { useEffect, useState } from "react";

/** Google redirect thẳng trình duyệt về "/" kèm ?google_connected=... hoặc
 * ?google_error=... (xem apps/teacher/views.py GoogleCallbackView) - đọc 1 lần
 * rồi dọn query string khỏi URL để refresh không hiện lại banner. */
export function GoogleCallbackBanner() {
  const [message, setMessage] = useState<{ tone: "success" | "danger"; text: string } | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const connected = params.get("google_connected");
    const error = params.get("google_error");

    if (connected) {
      setMessage({ tone: "success", text: `Đã kết nối Google Calendar (${connected}).` });
    } else if (error) {
      setMessage({ tone: "danger", text: error });
    }

    if (connected || error) {
      params.delete("google_connected");
      params.delete("google_error");
      const rest = params.toString();
      window.history.replaceState({}, "", window.location.pathname + (rest ? `?${rest}` : ""));
    }
  }, []);

  if (!message) return null;

  return (
    <div
      style={{
        margin: "0 32px 16px",
        padding: "12px 18px",
        borderRadius: "var(--radius-md)",
        background: message.tone === "success" ? "var(--success-bg)" : "var(--danger-bg)",
        color: message.tone === "success" ? "var(--success)" : "var(--danger)",
        fontWeight: 600,
        fontSize: "0.9rem",
      }}
    >
      {message.text}
    </div>
  );
}
