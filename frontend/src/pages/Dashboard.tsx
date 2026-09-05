import styles from "./Dashboard.module.css";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { StatTile } from "../components/ui/StatTile";
import { SectionHeading } from "../components/ui/SectionHeading";
import { Doodle } from "../components/ui/Doodle";
import { students, sessions, notifications, monthlyReports } from "../data/mockData";

function formatVND(amount: number) {
  return amount.toLocaleString("vi-VN") + " đ";
}

function formatShortDate(iso: string) {
  const d = new Date(iso);
  return d.toLocaleDateString("vi-VN", { day: "2-digit", month: "2-digit" });
}

function timeAgo(iso: string) {
  const diffMs = Date.now() - new Date(iso).getTime();
  const hours = Math.round(diffMs / 36e5);
  if (hours < 1) return "vừa xong";
  if (hours < 24) return `${hours} giờ trước`;
  return `${Math.round(hours / 24)} ngày trước`;
}

export function Dashboard() {
  const activeStudents = students.filter((s) => s.status === "active").length;
  const upcoming = sessions
    .filter((s) => new Date(`${s.date}T${s.startTime}`) >= new Date("2026-09-05T00:00:00"))
    .sort((a, b) => `${a.date}${a.startTime}`.localeCompare(`${b.date}${b.startTime}`))
    .slice(0, 5);
  const pendingAttendance = sessions.filter((s) => s.attendance === null && s.date <= "2026-09-05").length;
  const unreadCount = notifications.filter((n) => !n.isRead).length;
  const lastMonthRevenue = monthlyReports.reduce((sum, r) => sum + r.totalAmount, 0);

  return (
    <div className={styles.page}>
      <SectionHeading title="Tổng quan" subtitle="Mọi thứ hôm nay của lớp học, gói gọn trong một trang." />

      <div className={styles.statGrid}>
        <StatTile
          icon={<Doodle kind="heart" color="var(--pastel-pink-deep)" size={20} />}
          iconBg="var(--pastel-pink)"
          value={activeStudents}
          label="Học viên đang học"
        />
        <StatTile
          icon={<Doodle kind="leaf" color="var(--mint-green-deep)" size={20} />}
          iconBg="var(--mint-green)"
          value={upcoming.length}
          label="Buổi học sắp tới"
        />
        <StatTile
          icon={<Doodle kind="sun" color="#b8860b" size={20} />}
          iconBg="var(--pastel-yellow)"
          value={pendingAttendance}
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
          <div className={styles.list}>
            {upcoming.map((s) => (
              <div key={s.id} className={styles.sessionRow}>
                <div className={styles.sessionDate}>{formatShortDate(s.date)}</div>
                <div className={styles.sessionInfo}>
                  <div className={styles.sessionName}>{s.studentName}</div>
                  <div className={styles.sessionTime}>
                    {s.startTime} - {s.endTime}
                  </div>
                </div>
                {s.status === "rescheduled" && <Badge tone="warning">Đã dời lịch</Badge>}
                {s.googleSynced ? (
                  <Badge tone="info">Đã đồng bộ</Badge>
                ) : (
                  <Badge tone="neutral">Chưa đồng bộ</Badge>
                )}
              </div>
            ))}
          </div>
        </Card>

        <Card tint="lavender">
          <SectionHeading title="Thông báo gần đây" doodleColor="var(--pastel-blue-deep)" />
          <div className={styles.list}>
            {notifications.slice(0, 4).map((n) => (
              <div key={n.id} className={styles.notifRow}>
                {!n.isRead && <span className={styles.notifUnreadDot} />}
                <div>
                  <div>{n.message}</div>
                  <div className={styles.notifTime}>{timeAgo(n.createdAt)}</div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <Card tint="peach">
        <SectionHeading title="Học phí tháng gần nhất" doodleColor="var(--peach-deep)" />
        <p style={{ color: "var(--ink-soft)", fontSize: "0.92rem" }}>
          Tổng học phí đã xuất báo cáo tháng trước:{" "}
          <strong style={{ color: "var(--ink)" }}>{formatVND(lastMonthRevenue)}</strong> từ{" "}
          {monthlyReports.length} học viên.
        </p>
      </Card>
    </div>
  );
}
