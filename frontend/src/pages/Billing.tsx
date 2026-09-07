import { useEffect, useState } from "react";
import styles from "./Billing.module.css";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { SectionHeading } from "../components/ui/SectionHeading";
import { useAsync } from "../hooks/useAsync";
import { listStudents } from "../api/students";
import { generateReport, listMonthlyReports, previewReport } from "../api/billing";
import { API_BASE_URL, ApiError } from "../api/client";

function formatVND(amount: number) {
  return amount.toLocaleString("vi-VN") + " đ";
}

const today = new Date();

export function Billing() {
  const [studentId, setStudentId] = useState<string>("");
  const [month, setMonth] = useState(today.getMonth() + 1);
  const [year, setYear] = useState(today.getFullYear());
  const [generating, setGenerating] = useState<"pdf" | "png" | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const { data: students } = useAsync(() => listStudents({ status: "active" }), []);

  useEffect(() => {
    if (!studentId && students && students.length > 0) setStudentId(students[0].id);
  }, [students, studentId]);

  const {
    data: preview,
    loading: previewLoading,
    error: previewError,
  } = useAsync(() => (studentId ? previewReport(studentId, month, year) : Promise.resolve(null)), [
    studentId,
    month,
    year,
  ]);

  const {
    data: reports,
    loading: reportsLoading,
    error: reportsError,
    refetch: refetchReports,
  } = useAsync(() => listMonthlyReports(), []);

  async function handleGenerate(format: "pdf" | "png") {
    if (!studentId) return;
    setGenerating(format);
    setActionError(null);
    try {
      await generateReport(studentId, month, year, format);
      refetchReports();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Không xuất được báo cáo.");
    } finally {
      setGenerating(null);
    }
  }

  return (
    <div className={styles.page}>
      <SectionHeading
        title="Học phí"
        subtitle="Xem trước và xuất báo cáo học phí theo tháng cho từng học viên."
        doodleColor="var(--lilac-deep)"
      />

      {actionError && (
        <Card>
          <p style={{ color: "var(--danger)" }}>{actionError}</p>
        </Card>
      )}

      <div className={styles.columns}>
        <Card tint="lavender">
          <SectionHeading title="Xem trước báo cáo" doodleColor="var(--lilac-deep)" />
          <div className={styles.formRow}>
            <select className={styles.select} value={studentId} onChange={(e) => setStudentId(e.target.value)}>
              {(students ?? []).map((s) => (
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
              {[today.getFullYear() - 1, today.getFullYear()].map((y) => (
                <option key={y} value={y}>
                  {y}
                </option>
              ))}
            </select>
          </div>

          {previewError && <p style={{ color: "var(--danger)" }}>{previewError}</p>}
          {previewLoading && <p style={{ color: "var(--ink-soft)" }}>Đang tải...</p>}

          {preview && (
            <>
              <table className={styles.previewTable}>
                <thead>
                  <tr>
                    <th>Ngày</th>
                    <th>Giờ</th>
                    <th>Trạng thái</th>
                  </tr>
                </thead>
                <tbody>
                  {preview.sessions.length === 0 ? (
                    <tr>
                      <td colSpan={3} style={{ color: "var(--ink-soft)", padding: "16px 10px" }}>
                        Không có buổi học nào trong tháng này.
                      </td>
                    </tr>
                  ) : (
                    preview.sessions.map((s, i) => (
                      <tr key={i}>
                        <td>{new Date(`${s.session_date}T00:00:00`).toLocaleDateString("vi-VN")}</td>
                        <td>{s.start_time.slice(0, 5)}</td>
                        <td>
                          <Badge tone={s.billable ? "success" : "neutral"}>{s.status}</Badge>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>

              <div className={styles.totalLine}>
                <span>Tổng buổi tính phí: {preview.total_sessions}</span>
                <span>{formatVND(preview.total_amount)}</span>
              </div>

              <div style={{ marginTop: 16, display: "flex", gap: 10 }}>
                <Button variant="primary" onClick={() => handleGenerate("pdf")} disabled={generating !== null}>
                  {generating === "pdf" ? "Đang xuất..." : "Xuất PDF"}
                </Button>
                <Button variant="soft" onClick={() => handleGenerate("png")} disabled={generating !== null}>
                  {generating === "png" ? "Đang xuất..." : "Xuất PNG"}
                </Button>
              </div>
            </>
          )}
        </Card>

        <Card tint="peach">
          <SectionHeading title="Báo cáo đã xuất" doodleColor="var(--peach-deep)" />
          {reportsError && <p style={{ color: "var(--danger)" }}>{reportsError}</p>}
          {reportsLoading && <p style={{ color: "var(--ink-soft)" }}>Đang tải...</p>}
          {!reportsLoading && (reports ?? []).length === 0 && (
            <p style={{ color: "var(--ink-soft)" }}>Chưa có báo cáo nào được xuất.</p>
          )}
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {(reports ?? []).map((r) => (
              <div key={r.id} className={styles.reportRow}>
                <div>
                  <div className={styles.reportName}>{r.student_name}</div>
                  <div className={styles.reportMeta}>
                    Tháng {r.month.toString().padStart(2, "0")}/{r.year} · {r.total_sessions} buổi
                  </div>
                </div>
                <div className={styles.reportAmount}>{formatVND(Number(r.total_amount))}</div>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => window.open(`${API_BASE_URL}${r.download_url}`, "_blank")}
                >
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
