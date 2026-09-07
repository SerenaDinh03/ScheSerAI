import styles from "./Dashboard.module.css";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { StatTile } from "../components/ui/StatTile";
import { SectionHeading } from "../components/ui/SectionHeading";
import { Doodle } from "../components/ui/Doodle";
import { useAsync } from "../hooks/useAsync";
import { listStudents } from "../api/students";
import { listSessions } from "../api/scheduling";
import { listNotifications } from "../api/notifications";
import { listMonthlyReports } from "../api/billing";

function formatVND(amount: number) {
  return amount.toLocaleString("vi-VN") + " đ";
}

function formatShortDate(iso: string) {
  const d = new Date(`${iso}T00:00:00`);
  return d.toLocaleDateString("vi-VN", { day: "2-digit", month: "2-digit" });
}

function timeAgo(iso: string) {
  const diffMs = Date.now() - new Date(iso).getTime();
  const hours = Math.round(diffMs / 36e5);
  if (hours < 1) return "vừa xong";
  if (hours < 24) return `${hours} giờ trước`;
  return `${Math.round(hours / 24)} ngày trước`;
}

const todayIso = () => new Date().toISOString().slice(0, 10);

export function Dashboard() {
  const { data: students, loading: loadingStudents, error: errorStudents } = useAsync(
    () => listStudents({ status: "active" }),
    [],
  );
  const { data: upcoming, loading: loadingUpcoming, error: errorUpcoming } = useAsync(
    () => listSessions({ date_from: todayIso() }),
    [],
  );
  const { data: pending } = useAsync(() => listSessions({ pending: true }), []);
  const { data: notifications, loading: loadingNotif, error: errorNotif } = useAsync(
    () => listNotifications(),
    [],
  );
  const { data: reports } = useAsync(() => listMonthlyReports(), []);

  const error = errorStudents || errorUpcoming || errorNotif;
  const loading = loadingStudents || loadingUpcoming || loadingNotif;

  if (error) {
    return (
      <Card>
        <p style={{ color: "var(--danger)" }}>Không tải được dữ liệu tổng quan: {error}</p>
      </Card>
    );
  }

  const upcomingSorted = [...(upcoming ?? [])]
    .sort((a, b) => `${a.session_date}${a.start_time}`.localeCompare(`${b.session_date}${b.start_time}`))
    .slice(0, 5);

  const unreadCount = (notifications ?? []).filter((n) => !n.is_read).length;

  const latestReports = reports ?? [];
  const latestKey = latestReports[0] ? `${latestReports[0].year}-${latestReports[0].month}` : null;
  const latestGroup = latestReports.filter((r) => `${r.year}-${r.month}` === latestKey);
  const latestRevenue = latestGroup.reduce((sum, r) => sum + Number(r.total_amount), 0);

  return (
    <div className={styles.page}>
      <SectionHeading title="Tổng quan" subtitle="Mọi thứ hôm nay của lớp học, gói gọn trong một trang." />

      {loading ? (
        <Card>
          <p style={{ color: "var(--ink-soft)" }}>Đang tải...</p>
        </Card>
      ) : (
        <>
          <div className={styles.statGrid}>
            <StatTile
              icon={<Doodle kind="heart" color="var(--pastel-pink-deep)" size={20} />}
              iconBg="var(--pastel-pink)"
              value={students?.length ?? 0}
              label="Học viên đang học"
            />
            <StatTile
              icon={<Doodle kind="leaf" color="var(--mint-green-deep)" size={20} />}
              iconBg="var(--mint-green)"
              value={upcoming?.length ?? 0}
              label="Buổi học sắp tới"
            />
            <StatTile
              icon={<Doodle kind="sun" color="#b8860b" size={20} />}
              iconBg="var(--pastel-yellow)"
              value={pending?.length ?? 0}
              label="Chờ điểm danh"
            />
            <StatTile
              icon={<Doodle kind="sparkle" color="var(--lilac-deep)" size={20} />}
              iconBg="var(--lilac)"
              value={unreadCount}
              label="Thông báo chưa đọc"
            />
          </div>

          <div className={styles.columns}>
            <Card tint="mint">
              <SectionHeading title="Buổi học sắp tới" doodleColor="var(--mint-green-deep)" />
              {upcomingSorted.length === 0 ? (
                <p style={{ color: "var(--ink-soft)" }}>Không có buổi học nào sắp tới.</p>
              ) : (
                <div className={styles.list}>
                  {upcomingSorted.map((s) => (
                    <div key={s.id} className={styles.sessionRow}>
                      <div className={styles.sessionDate}>{formatShortDate(s.session_date)}</div>
                      <div className={styles.sessionInfo}>
                        <div className={styles.sessionName}>{s.student_name}</div>
                        <div className={styles.sessionTime}>
                          {s.start_time.slice(0, 5)} - {s.end_time.slice(0, 5)}
                        </div>
                      </div>
                      {s.status === "rescheduled" && <Badge tone="warning">Đã dời lịch</Badge>}
                      {s.google_event_id ? (
                        <Badge tone="info">Đã đồng bộ</Badge>
                      ) : (
                        <Badge tone="neutral">Chưa đồng bộ</Badge>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </Card>

            <Card tint="lavender">
              <SectionHeading title="Thông báo gần đây" doodleColor="var(--pastel-blue-deep)" />
              {(notifications ?? []).length === 0 ? (
                <p style={{ color: "var(--ink-soft)" }}>Chưa có thông báo nào.</p>
              ) : (
                <div className={styles.list}>
                  {(notifications ?? []).slice(0, 4).map((n) => (
                    <div key={n.id} className={styles.notifRow}>
                      {!n.is_read && <span className={styles.notifUnreadDot} />}
                      <div>
                        <div>{n.message}</div>
                        <div className={styles.notifTime}>{timeAgo(n.created_at)}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </div>

          {latestGroup.length > 0 && (
            <Card tint="peach">
              <SectionHeading title="Học phí tháng gần nhất" doodleColor="var(--peach-deep)" />
              <p style={{ color: "var(--ink-soft)", fontSize: "0.92rem" }}>
                Tổng học phí đã xuất báo cáo tháng {latestGroup[0].month.toString().padStart(2, "0")}/
                {latestGroup[0].year}:{" "}
                <strong style={{ color: "var(--ink)" }}>{formatVND(latestRevenue)}</strong> từ{" "}
                {latestGroup.length} học viên.
              </p>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
