import styles from "./Notifications.module.css";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { SectionHeading } from "../components/ui/SectionHeading";
import { useAsync } from "../hooks/useAsync";
import { listNotifications, markAllNotificationsRead, markNotificationRead } from "../api/notifications";

function timeLabel(iso: string) {
  return new Date(iso).toLocaleString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function Notifications() {
  const { data: items, loading, error, refetch } = useAsync(() => listNotifications(), []);
  const unreadCount = (items ?? []).filter((n) => !n.is_read).length;

  async function markRead(id: string) {
    await markNotificationRead(id);
    refetch();
  }

  async function markAllRead() {
    await markAllNotificationsRead();
    refetch();
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

      {error && (
        <Card>
          <p style={{ color: "var(--danger)" }}>Không tải được thông báo: {error}</p>
        </Card>
      )}

      {!error && loading && (
        <Card>
          <p style={{ color: "var(--ink-soft)" }}>Đang tải...</p>
        </Card>
      )}

      {!error && !loading && (
        <Card>
          {(items ?? []).length === 0 ? (
            <p style={{ color: "var(--ink-soft)" }}>Chưa có thông báo nào.</p>
          ) : (
            <div className={styles.list}>
              {(items ?? []).map((n) => (
                <div
                  key={n.id}
                  className={`${styles.row} ${!n.is_read ? styles.rowUnread : ""}`}
                  onClick={() => !n.is_read && markRead(n.id)}
                  role="button"
                  tabIndex={0}
                >
                  <span className={`${styles.dot} ${n.is_read ? styles.dotRead : ""}`} />
                  <div className={styles.message}>
                    {n.message}
                    <div className={styles.time}>{timeLabel(n.created_at)}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
