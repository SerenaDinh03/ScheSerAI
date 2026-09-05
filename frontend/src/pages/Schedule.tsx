import { useMemo, useState } from "react";
import styles from "./Schedule.module.css";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { SectionHeading } from "../components/ui/SectionHeading";
import { sessions as initialSessions } from "../data/mockData";
import type { AttendanceStatus, Session } from "../types";

const TODAY = "2026-09-05";
const WEEKDAYS = ["Chủ Nhật", "Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy"];

function dayLabel(dateStr: string) {
  const d = new Date(`${dateStr}T00:00:00`);
  const prefix = dateStr === TODAY ? "Hôm nay · " : "";
  return `${prefix}${WEEKDAYS[d.getDay()]}, ${d.toLocaleDateString("vi-VN")}`;
}

export function Schedule() {
  const [sessions, setSessions] = useState<Session[]>(initialSessions);

  const grouped = useMemo(() => {
    const byDate = new Map<string, Session[]>();
    [...sessions]
      .sort((a, b) => `${a.date}${a.startTime}`.localeCompare(`${b.date}${b.startTime}`))
      .forEach((s) => {
        const list = byDate.get(s.date) ?? [];
        list.push(s);
        byDate.set(s.date, list);
      });
    return Array.from(byDate.entries());
  }, [sessions]);

  function markAttendance(id: string, status: AttendanceStatus) {
    setSessions((prev) => prev.map((s) => (s.id === id ? { ...s, attendance: status } : s)));
  }

  function cancelSession(id: string) {
    setSessions((prev) => prev.filter((s) => s.id !== id));
  }

  return (
    <div className={styles.page}>
      <SectionHeading
        title="Lịch dạy"
        subtitle="Điểm danh, dời lịch hoặc hủy buổi học ngay tại đây."
        doodleColor="var(--mint-green-deep)"
        actions={<Button variant="soft">+ Tạo lịch cố định</Button>}
      />

      {grouped.map(([date, daySessions]) => (
        <div key={date} className={styles.dayGroup}>
          <div className={styles.dayLabel}>{dayLabel(date)}</div>
          {daySessions.map((s) => {
            const hasStarted = `${s.date}${s.startTime}` <= `${TODAY}23:59`;
            const canMarkFirst = hasStarted && s.attendance === null;
            return (
              <div key={s.id} className={styles.row}>
                <div className={styles.time}>
                  {s.startTime}–{s.endTime}
                </div>
                <div className={styles.student}>{s.studentName}</div>
                <div className={styles.badges}>
                  {s.status === "rescheduled" && <Badge tone="warning">Đã dời lịch</Badge>}
                  {s.attendance === "present" && <Badge tone="success">Có mặt</Badge>}
                  {s.attendance === "absent" && <Badge tone="danger">Vắng</Badge>}
                  {s.attendance === null && hasStarted && <Badge tone="warning">Chưa điểm danh</Badge>}
                  {s.googleSynced && <Badge tone="info">📅 Đồng bộ</Badge>}
                </div>
                <div className={styles.actions}>
                  {(canMarkFirst || s.attendance !== null) && (
                    <>
                      <Button size="sm" variant="soft" onClick={() => markAttendance(s.id, "present")}>
                        Có mặt
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => markAttendance(s.id, "absent")}>
                        Vắng
                      </Button>
                    </>
                  )}
                  <Button size="sm" variant="danger" onClick={() => cancelSession(s.id)} disabled={s.attendance !== null}>
                    Hủy
                  </Button>
                </div>
              </div>
            );
          })}
        </div>
      ))}

      {sessions.length === 0 && (
        <Card>
          <div style={{ textAlign: "center", color: "var(--ink-soft)", padding: 40 }}>
            Không còn buổi học nào trong danh sách. ✨
          </div>
        </Card>
      )}
    </div>
  );
}
