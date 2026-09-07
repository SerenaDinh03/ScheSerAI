import { Link } from "react-router-dom";
import styles from "./TopBar.module.css";
import { useAuth } from "../../context/AuthContext";
import { useAsync } from "../../hooks/useAsync";
import { unreadCount } from "../../api/notifications";
import { disconnectGoogle, googleStatus } from "../../api/teacher";
import { API_BASE_URL } from "../../api/client";

const WEEKDAYS = ["Chủ Nhật", "Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy"];

function todayLabel() {
  const now = new Date();
  return `${WEEKDAYS[now.getDay()]}, ${now.toLocaleDateString("vi-VN")}`;
}

function initials(name: string) {
  const parts = name.trim().split(/\s+/);
  return parts[parts.length - 1]?.[0]?.toUpperCase() ?? "?";
}

export function TopBar() {
  const { user } = useAuth();
  const { data: unread } = useAsync(() => unreadCount(), []);
  const { data: google, refetch: refetchGoogle } = useAsync(() => googleStatus(), []);

  const displayName = user?.name || user?.username || "";

  async function handleDisconnect() {
    if (!window.confirm("Ngắt kết nối Google Calendar? Các buổi học mới sẽ không tự đồng bộ nữa.")) {
      return;
    }
    await disconnectGoogle();
    refetchGoogle();
  }

  return (
    <header className={styles.bar}>
      <div className={styles.greeting}>
        <span className={styles.hello}>Chào buổi sáng, {displayName} 👋</span>
        <span className={styles.date}>{todayLabel()}</span>
      </div>

      <div className={styles.right}>
        {google?.connected ? (
          <button
            className={`${styles.googlePill} ${styles.googlePillAction}`}
            onClick={handleDisconnect}
            title="Bấm để ngắt kết nối"
          >
            <span className={styles.dot} style={{ background: "var(--mint-green-deep)" }} />
            Google Calendar đã kết nối ({google.email}) · Ngắt kết nối
          </button>
        ) : (
          <button
            className={`${styles.googlePill} ${styles.googlePillAction}`}
            onClick={() => {
              window.location.href = `${API_BASE_URL}/api/google/connect/`;
            }}
          >
            <span className={styles.dot} style={{ background: "var(--pastel-pink-deep)" }} />
            Chưa kết nối Google · Bấm để kết nối
          </button>
        )}

        <Link to="/notifications" className={styles.bell} aria-label="Thông báo">
          🔔
          {!!unread?.count && <span className={styles.bellCount}>{unread.count}</span>}
        </Link>

        <div className={styles.avatar}>{initials(displayName || "?")}</div>
      </div>
    </header>
  );
}
