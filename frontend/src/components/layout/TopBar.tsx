import { Link } from "react-router-dom";
import styles from "./TopBar.module.css";
import { teacher, notifications } from "../../data/mockData";

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
  const unread = notifications.filter((n) => !n.isRead).length;

  return (
    <header className={styles.bar}>
      <div className={styles.greeting}>
        <span className={styles.hello}>Chào buổi sáng, {teacher.name} 👋</span>
        <span className={styles.date}>{todayLabel()}</span>
      </div>

      <div className={styles.right}>
        <span className={styles.googlePill}>
          <span
            className={styles.dot}
            style={{ background: teacher.googleConnected ? "var(--mint-green-deep)" : "var(--pastel-pink-deep)" }}
          />
          {teacher.googleConnected ? "Google Calendar đã kết nối" : "Chưa kết nối Google"}
        </span>

        <Link to="/notifications" className={styles.bell} aria-label="Thông báo">
          🔔
          {unread > 0 && <span className={styles.bellCount}>{unread}</span>}
        </Link>

        <div className={styles.avatar}>{initials(teacher.name)}</div>
      </div>
    </header>
  );
}
