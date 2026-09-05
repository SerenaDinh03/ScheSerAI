import { useMemo, useState } from "react";
import styles from "./Billing.module.css";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { SectionHeading } from "../components/ui/SectionHeading";
import { students, sessions, monthlyReports } from "../data/mockData";

function formatVND(amount: number) {
  return amount.toLocaleString("vi-VN") + " đ";
}

export function Billing() {
  const [studentId, setStudentId] = useState(students[0].id);
  const [month, setMonth] = useState(9);
  const [year, setYear] = useState(2026);

  const student = students.find((s) => s.id === studentId)!;

  const previewRows = useMemo(() => {
    return sessions
      .filter((s) => {
        const d = new Date(`${s.date}T00:00:00`);
        return s.studentId === studentId && d.getMonth() + 1 === month && d.getFullYear() === year;
      })
      .sort((a, b) => `${a.date}${a.startTime}`.localeCompare(`${b.date}${b.startTime}`));
  }, [studentId, month, year]);

  const billableCount = previewRows.filter((s) => s.attendance === "present").length;
  const totalAmount = billableCount * student.pricePerSession;

  return (
    <div className={styles.page}>
      <SectionHeading
        title="Học phí"
        subtitle="Xem trước và xuất báo cáo học phí theo tháng cho từng học viên."
        doodleColor="var(--lilac-deep)"
      />

      <div className={styles.columns}>
        <Card tint="lavender">
          <SectionHeading title="Xem trước báo cáo" doodleColor="var(--lilac-deep)" />
          <div className={styles.formRow}>
            <select className={styles.select} value={studentId} onChange={(e) => setStudentId(e.target.value)}>
              {students.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
            <select className={styles.select} value={month} onChange={(e) => setMonth(Number(e.target.value))}>
              {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                <option key={m} value={m}>
                  Tháng {m.toString().padStart(2, "0")}
                </option>
              ))}
            </select>
            <select className={styles.select} value={year} onChange={(e) => setYear(Number(e.target.value))}>
              {[2025, 2026].map((y) => (
                <option key={y} value={y}>
                  {y}
                </option>
              ))}
            </select>
          </div>

          <table className={styles.previewTable}>
            <thead>
              <tr>
                <th>Ngày</th>
                <th>Giờ</th>
                <th>Trạng thái</th>
              </tr>
            </thead>
            <tbody>
              {previewRows.length === 0 ? (
                <tr>
                  <td colSpan={3} style={{ color: "var(--ink-soft)", padding: "16px 10px" }}>
                    Không có buổi học nào trong tháng này.
                  </td>
                </tr>
              ) : (
                previewRows.map((s) => (
                  <tr key={s.id}>
                    <td>{new Date(s.date).toLocaleDateString("vi-VN")}</td>
                    <td>{s.startTime}</td>
                    <td>
                      {s.attendance === "present" && <Badge tone="success">Có mặt</Badge>}
                      {s.attendance === "absent" && <Badge tone="danger">Nghỉ</Badge>}
                      {s.attendance === null && <Badge tone="neutral">Chưa điểm danh</Badge>}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>

          <div className={styles.totalLine}>
            <span>Tổng buổi tính phí: {billableCount}</span>
            <span>{formatVND(totalAmount)}</span>
          </div>

          <div style={{ marginTop: 16, display: "flex", gap: 10 }}>
            <Button variant="primary">Xuất PDF</Button>
            <Button variant="soft">Xuất PNG</Button>
          </div>
        </Card>

        <Card tint="peach">
          <SectionHeading title="Báo cáo đã xuất" doodleColor="var(--peach-deep)" />
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {monthlyReports.map((r) => (
              <div key={r.id} className={styles.reportRow}>
                <div>
                  <div className={styles.reportName}>{r.studentName}</div>
                  <div className={styles.reportMeta}>
                    Tháng {r.month.toString().padStart(2, "0")}/{r.year} · {r.totalSessions} buổi ·{" "}
                    {r.format.toUpperCase()}
                  </div>
                </div>
                <div className={styles.reportAmount}>{formatVND(r.totalAmount)}</div>
                <Button size="sm" variant="ghost">
                  Tải xuống
                </Button>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
