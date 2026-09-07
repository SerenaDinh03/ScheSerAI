import { useMemo, useState } from "react";
import type { FormEvent } from "react";
import styles from "./Schedule.module.css";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { SectionHeading } from "../components/ui/SectionHeading";
import { useAsync } from "../hooks/useAsync";
import {
  cancelSession,
  createSchedule,
  createSession,
  listSchedules,
  listSessions,
  markAttendance,
  pauseSchedule,
  resumeSchedule,
  rescheduleSession,
} from "../api/scheduling";
import { listStudents } from "../api/students";
import { ApiError } from "../api/client";
import type { ApiAttendanceStatus } from "../api/types";

const WEEKDAYS = ["Chủ Nhật", "Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy"];

// Khớp DAY_OF_WEEK_CHOICES ở backend/apps/scheduling/models.py: 0=Thứ Hai..6=Chủ Nhật
// (theo date.weekday() của Python) - khác thứ tự getDay() của JS (0=Chủ Nhật).
const SCHEDULE_DAY_OPTIONS = [
  { value: 0, label: "Thứ Hai" },
  { value: 1, label: "Thứ Ba" },
  { value: 2, label: "Thứ Tư" },
  { value: 3, label: "Thứ Năm" },
  { value: 4, label: "Thứ Sáu" },
  { value: 5, label: "Thứ Bảy" },
  { value: 6, label: "Chủ Nhật" },
];

function isoDate(d: Date) {
  return d.toISOString().slice(0, 10);
}

function dayLabel(dateStr: string) {
  const d = new Date(`${dateStr}T00:00:00`);
  const isToday = dateStr === isoDate(new Date());
  return `${isToday ? "Hôm nay · " : ""}${WEEKDAYS[d.getDay()]}, ${d.toLocaleDateString("vi-VN")}`;
}

export function Schedule() {
  const [reschedulingId, setReschedulingId] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showAddSessionForm, setShowAddSessionForm] = useState(false);

  const dateFrom = useMemo(() => {
    const d = new Date();
    d.setDate(d.getDate() - 7);
    return isoDate(d);
  }, []);
  const dateTo = useMemo(() => {
    const d = new Date();
    d.setDate(d.getDate() + 21);
    return isoDate(d);
  }, []);

  const { data: sessions, loading, error, refetch } = useAsync(
    () => listSessions({ date_from: dateFrom, date_to: dateTo }),
    [dateFrom, dateTo],
  );

  const {
    data: schedules,
    loading: schedulesLoading,
    refetch: refetchSchedules,
  } = useAsync(() => listSchedules(), []);

  const grouped = useMemo(() => {
    const byDate = new Map<string, NonNullable<typeof sessions>>();
    [...(sessions ?? [])]
      .sort((a, b) => `${a.session_date}${a.start_time}`.localeCompare(`${b.session_date}${b.start_time}`))
      .forEach((s) => {
        const list = byDate.get(s.session_date) ?? [];
        list.push(s);
        byDate.set(s.session_date, list as NonNullable<typeof sessions>);
      });
    return Array.from(byDate.entries());
  }, [sessions]);

  async function handleMark(id: string, status: ApiAttendanceStatus) {
    setActionError(null);
    try {
      await markAttendance(id, status);
      refetch();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Không điểm danh được.");
    }
  }

  async function handleCancel(id: string) {
    if (!window.confirm("Hủy hẳn buổi học này? Không thể hoàn tác.")) return;
    setActionError(null);
    try {
      await cancelSession(id);
      refetch();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Không hủy được buổi học.");
    }
  }

  async function handleToggleSchedule(id: string, isActive: boolean) {
    setActionError(null);
    try {
      if (isActive) {
        await pauseSchedule(id);
      } else {
        await resumeSchedule(id);
      }
      refetchSchedules();
      refetch();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Không đổi được trạng thái lịch cố định.");
    }
  }

  return (
    <div className={styles.page}>
      <SectionHeading
        title="Lịch dạy"
        subtitle="Điểm danh, dời lịch hoặc hủy buổi học ngay tại đây."
        doodleColor="var(--mint-green-deep)"
        actions={
          <>
            <Button variant="ghost" onClick={() => setShowAddSessionForm((v) => !v)}>
              {showAddSessionForm ? "Đóng" : "+ Thêm buổi học"}
            </Button>
            <Button variant="soft" onClick={() => setShowCreateForm((v) => !v)}>
              {showCreateForm ? "Đóng" : "+ Tạo lịch cố định"}
            </Button>
          </>
        }
      />

      {actionError && <div className={styles.banner}>{actionError}</div>}

      {showAddSessionForm && (
        <AddSessionForm
          onCreated={() => {
            setShowAddSessionForm(false);
            refetch();
          }}
        />
      )}

      {showCreateForm && (
        <CreateScheduleForm
          onCreated={() => {
            setShowCreateForm(false);
            refetchSchedules();
            refetch();
          }}
        />
      )}

      <Card tint="lavender">
        <SectionHeading title="Lịch cố định hàng tuần" doodleColor="var(--lilac-deep)" />
        {schedulesLoading && <p style={{ color: "var(--ink-soft)" }}>Đang tải...</p>}
        {!schedulesLoading && (schedules ?? []).length === 0 && (
          <p style={{ color: "var(--ink-soft)" }}>Chưa có lịch cố định nào. Bấm "+ Tạo lịch cố định" để thêm.</p>
        )}
        <div className={styles.scheduleList}>
          {(schedules ?? []).map((sc) => (
            <div key={sc.id} className={styles.scheduleRow}>
              <span className={styles.scheduleStudent}>{sc.student_name}</span>
              <span className={styles.scheduleTime}>
                {sc.day_of_week_display} · {sc.start_time.slice(0, 5)}–{sc.end_time.slice(0, 5)}
              </span>
              <Badge tone={sc.is_active ? "success" : "neutral"}>
                {sc.is_active ? "Đang áp dụng" : "Đã tạm dừng"}
              </Badge>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => handleToggleSchedule(sc.id, sc.is_active)}
                style={{ marginLeft: "auto" }}
              >
                {sc.is_active ? "Tạm dừng" : "Kích hoạt lại"}
              </Button>
            </div>
          ))}
        </div>
      </Card>

      {error && (
        <Card>
          <p style={{ color: "var(--danger)" }}>Không tải được lịch dạy: {error}</p>
        </Card>
      )}

      {!error && loading && (
        <Card>
          <p style={{ color: "var(--ink-soft)" }}>Đang tải...</p>
        </Card>
      )}

      {!error &&
        !loading &&
        grouped.map(([date, daySessions]) => (
          <div key={date} className={styles.dayGroup}>
            <div className={styles.dayLabel}>{dayLabel(date)}</div>
            {daySessions.map((s) => {
              const hasStarted = `${s.session_date}T${s.start_time}` <= new Date().toISOString();
              const canMarkFirst = hasStarted && s.attendance === null;
              const isReschedulingThis = reschedulingId === s.id;
              return (
                <div key={s.id} className={styles.row}>
                  <div className={styles.time}>
                    {s.start_time.slice(0, 5)}–{s.end_time.slice(0, 5)}
                  </div>
                  <div className={styles.student}>{s.student_name}</div>
                  <div className={styles.badges}>
                    {s.status === "rescheduled" && <Badge tone="warning">Đã dời lịch</Badge>}
                    {s.attendance?.status === "present" && <Badge tone="success">Có mặt</Badge>}
                    {s.attendance?.status === "absent" && <Badge tone="danger">Vắng</Badge>}
                    {s.attendance === null && hasStarted && <Badge tone="warning">Chưa điểm danh</Badge>}
                    {s.google_event_id && <Badge tone="info">📅 Đồng bộ</Badge>}
                  </div>
                  <div className={styles.actions}>
                    {(canMarkFirst || s.attendance !== null) && (
                      <>
                        <Button size="sm" variant="soft" onClick={() => handleMark(s.id, "present")}>
                          Có mặt
                        </Button>
                        <Button size="sm" variant="ghost" onClick={() => handleMark(s.id, "absent")}>
                          Vắng
                        </Button>
                      </>
                    )}
                    <Button
                      size="sm"
                      variant="soft"
                      onClick={() => setReschedulingId(isReschedulingThis ? null : s.id)}
                    >
                      Dời lịch
                    </Button>
                    <Button
                      size="sm"
                      variant="danger"
                      onClick={() => handleCancel(s.id)}
                      disabled={s.attendance !== null}
                    >
                      Hủy
                    </Button>
                  </div>

                  {isReschedulingThis && (
                    <RescheduleForm
                      sessionId={s.id}
                      defaultDate={s.session_date}
                      defaultStartTime={s.start_time.slice(0, 5)}
                      onDone={() => {
                        setReschedulingId(null);
                        refetch();
                      }}
                      onError={(msg) => setActionError(msg)}
                    />
                  )}
                </div>
              );
            })}
          </div>
        ))}

      {!error && !loading && grouped.length === 0 && (
        <Card>
          <div style={{ textAlign: "center", color: "var(--ink-soft)", padding: 40 }}>
            Không có buổi học nào trong khoảng thời gian này. ✨
          </div>
        </Card>
      )}
    </div>
  );
}

function AddSessionForm({ onCreated }: { onCreated: () => void }) {
  const { data: students } = useAsync(() => listStudents({ status: "active" }), []);
  const [studentId, setStudentId] = useState("");
  const [sessionDate, setSessionDate] = useState(isoDate(new Date()));
  const [startTime, setStartTime] = useState("19:00");
  const [endTime, setEndTime] = useState("20:00");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const effectiveStudentId = studentId || students?.[0]?.id || "";

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!effectiveStudentId) {
      setError("Chưa có học viên nào - hãy thêm học viên trước.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await createSession({
        student: effectiveStudentId,
        session_date: sessionDate,
        start_time: startTime,
        end_time: endTime,
      });
      onCreated();
    } catch (err) {
      if (err instanceof ApiError && err.body && typeof err.body === "object") {
        const firstError = Object.values(err.body as Record<string, unknown>)[0];
        setError(Array.isArray(firstError) ? String(firstError[0]) : err.message);
      } else {
        setError(err instanceof Error ? err.message : "Không thêm được buổi học.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Card tint="peach">
      <SectionHeading
        title="Thêm buổi học lẻ"
        subtitle="Dùng cho buổi đã dạy trước khi vào hệ thống, hoặc buổi phát sinh ngoài lịch cố định."
        doodleColor="var(--peach-deep)"
      />
      <form className={styles.form} onSubmit={handleSubmit}>
        {error && <div className={styles.error}>{error}</div>}

        <div className={styles.formField}>
          <label className={styles.formLabel}>Học viên *</label>
          <select
            className={styles.input}
            value={effectiveStudentId}
            onChange={(e) => setStudentId(e.target.value)}
          >
            {(students ?? []).map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </div>
        <div className={styles.formField}>
          <label className={styles.formLabel}>Ngày học *</label>
          <input
            type="date"
            className={styles.input}
            value={sessionDate}
            onChange={(e) => setSessionDate(e.target.value)}
            required
          />
        </div>
        <div className={styles.formField}>
          <label className={styles.formLabel}>Giờ bắt đầu *</label>
          <input
            type="time"
            className={styles.input}
            value={startTime}
            onChange={(e) => setStartTime(e.target.value)}
            required
          />
        </div>
        <div className={styles.formField}>
          <label className={styles.formLabel}>Giờ kết thúc *</label>
          <input
            type="time"
            className={styles.input}
            value={endTime}
            onChange={(e) => setEndTime(e.target.value)}
            required
          />
        </div>

        <div className={styles.formActions}>
          <Button type="submit" variant="primary" disabled={submitting}>
            {submitting ? "Đang lưu..." : "Lưu buổi học"}
          </Button>
        </div>
      </form>
    </Card>
  );
}

function CreateScheduleForm({ onCreated }: { onCreated: () => void }) {
  const { data: students } = useAsync(() => listStudents({ status: "active" }), []);
  const [studentId, setStudentId] = useState("");
  const [dayOfWeek, setDayOfWeek] = useState(3);
  const [startTime, setStartTime] = useState("19:00");
  const [endTime, setEndTime] = useState("20:30");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const effectiveStudentId = studentId || students?.[0]?.id || "";

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!effectiveStudentId) {
      setError("Chưa có học viên nào - hãy thêm học viên trước.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await createSchedule({
        student: effectiveStudentId,
        day_of_week: dayOfWeek,
        start_time: startTime,
        end_time: endTime,
      });
      onCreated();
    } catch (err) {
      if (err instanceof ApiError && err.body && typeof err.body === "object") {
        const firstError = Object.values(err.body as Record<string, unknown>)[0];
        setError(Array.isArray(firstError) ? String(firstError[0]) : err.message);
      } else {
        setError(err instanceof Error ? err.message : "Không tạo được lịch cố định.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Card tint="mint">
      <SectionHeading title="Tạo lịch cố định hàng tuần" doodleColor="var(--mint-green-deep)" />
      <form className={styles.form} onSubmit={handleSubmit}>
        {error && <div className={styles.error}>{error}</div>}

        <div className={styles.formField}>
          <label className={styles.formLabel}>Học viên *</label>
          <select
            className={styles.input}
            value={effectiveStudentId}
            onChange={(e) => setStudentId(e.target.value)}
          >
            {(students ?? []).map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </div>
        <div className={styles.formField}>
          <label className={styles.formLabel}>Thứ trong tuần *</label>
          <select
            className={styles.input}
            value={dayOfWeek}
            onChange={(e) => setDayOfWeek(Number(e.target.value))}
          >
            {SCHEDULE_DAY_OPTIONS.map((d) => (
              <option key={d.value} value={d.value}>
                {d.label}
              </option>
            ))}
          </select>
        </div>
        <div className={styles.formField}>
          <label className={styles.formLabel}>Giờ bắt đầu *</label>
          <input
            type="time"
            className={styles.input}
            value={startTime}
            onChange={(e) => setStartTime(e.target.value)}
            required
          />
        </div>
        <div className={styles.formField}>
          <label className={styles.formLabel}>Giờ kết thúc *</label>
          <input
            type="time"
            className={styles.input}
            value={endTime}
            onChange={(e) => setEndTime(e.target.value)}
            required
          />
        </div>

        <div className={styles.formActions}>
          <Button type="submit" variant="primary" disabled={submitting}>
            {submitting ? "Đang lưu..." : "Lưu lịch cố định"}
          </Button>
        </div>
      </form>
    </Card>
  );
}

function RescheduleForm({
  sessionId,
  defaultDate,
  defaultStartTime,
  onDone,
  onError,
}: {
  sessionId: string;
  defaultDate: string;
  defaultStartTime: string;
  onDone: () => void;
  onError: (message: string) => void;
}) {
  const [date, setDate] = useState(defaultDate);
  const [time, setTime] = useState(defaultStartTime);
  const [submitting, setSubmitting] = useState(false);

  async function handleConfirm() {
    setSubmitting(true);
    try {
      await rescheduleSession(sessionId, { session_date: date, start_time: time });
      onDone();
    } catch (err) {
      onError(err instanceof ApiError ? err.message : "Không dời lịch được.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className={styles.rescheduleForm}>
      <input
        type="date"
        className={styles.rescheduleInput}
        value={date}
        onChange={(e) => setDate(e.target.value)}
      />
      <input
        type="time"
        className={styles.rescheduleInput}
        value={time}
        onChange={(e) => setTime(e.target.value)}
      />
      <Button size="sm" variant="primary" onClick={handleConfirm} disabled={submitting}>
        {submitting ? "Đang lưu..." : "Xác nhận"}
      </Button>
    </div>
  );
}
