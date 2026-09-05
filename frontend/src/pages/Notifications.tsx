import { useState } from "react";
import styles from "./Notifications.module.css";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { SectionHeading } from "../components/ui/SectionHeading";
import { notifications as initialNotifications } from "../data/mockData";

function timeLabel(iso: string) {
  return new Date(iso).toLocaleString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function Notifications() {
  const [items, setItems] = useState(initialNotifications);
  const unreadCount = items.filter((n) => !n.isRead).length;

  function markRead(id: string) {
    setItems((prev) => prev.map((n) => (n.id === id ? { ...n, isRead: true } : n)));
  }

  function markAllRead() {
    setItems((prev) => prev.map((n) => ({ ...n, isRead: true })));
  }

  return (
    <div className={styles.page}>
      <SectionHeading
        title="Thông báo"
        subtitle={unreadCount > 0 ? `Bạn có ${unreadCount} thông báo chưa đọc` : "Bạn đã đọc hết thông báo ✨"}
        doodleColor="var(--pastel-blue-deep)"
        actions={
          <Button variant="soft" size="sm" onClick={markAllRead} disabled={unreadCount === 0}>
            Đánh dấu tất cả đã đọc
          </Button>
        }
      />

      <Card>
        <div className={styles.list}>
          {items.map((n) => (
            <div
              key={n.id}
              className={`${styles.row} ${!n.isRead ? styles.rowUnread : ""}`}
              onClick={() => markRead(n.id)}
              role="button"
              tabIndex={0}
            >
              <span className={`${styles.dot} ${n.isRead ? styles.dotRead : ""}`} />
              <div className={styles.message}>
                {n.message}
                <div className={styles.time}>{timeLabel(n.createdAt)}</div>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
