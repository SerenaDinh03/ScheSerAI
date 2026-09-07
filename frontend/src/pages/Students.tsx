import { useState } from "react";
import type { FormEvent } from "react";
import styles from "./Students.module.css";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { SectionHeading } from "../components/ui/SectionHeading";
import { useAsync } from "../hooks/useAsync";
import { createStudent, deactivateStudent, getStudent, listStudents, updateStudent } from "../api/students";
import { ApiError } from "../api/client";
import type { ApiStudentDetail, ApiStudentStatus } from "../api/types";

const AVATAR_COLORS = ["var(--pastel-pink)", "var(--mint-green)", "var(--powder-blue)", "var(--lilac)", "var(--peach)"];

function initials(name: string) {
  const parts = name.trim().split(/\s+/);
  return parts[parts.length - 1]?.[0]?.toUpperCase() ?? "?";
}

function formatVND(amount: number) {
  return amount.toLocaleString("vi-VN") + " đ";
}

type Filter = "all" | ApiStudentStatus;

export function Students() {
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<Filter>("active");
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<ApiStudentDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);

  const {
    data: students,
    loading,
    error,
    refetch,
  } = useAsync(async () => {
    if (filter === "all") {
      const [active, inactive] = await Promise.all([
        listStudents({ status: "active", search: query || undefined }),
        listStudents({ status: "inactive", search: query || undefined }),
      ]);
      return [...active, ...inactive].sort((a, b) => a.name.localeCompare(b.name));
    }
    return listStudents({ status: filter, search: query || undefined });
  }, [filter, query]);

  async function toggleExpand(id: string) {
    if (expandedId === id) {
      setExpandedId(null);
      setDetail(null);
      setEditingId(null);
      return;
    }
    setExpandedId(id);
    setDetail(null);
    setEditingId(null);
    setDetailLoading(true);
    try {
      const d = await getStudent(id);
      setDetail(d);
    } finally {
      setDetailLoading(false);
    }
  }

  async function reloadDetail(id: string) {
    const d = await getStudent(id);
    setDetail(d);
  }

  async function handleDeactivate(id: string, name: string) {
    if (!window.confirm(`Cho ${name} tạm nghỉ? Các buổi học sắp tới của bạn ấy sẽ bị xóa.`)) return;
    await deactivateStudent(id);
    await reloadDetail(id);
    refetch();
  }

  return (
    <div className={styles.page}>
      <SectionHeading
        title="Học viên"
        subtitle={`${(students ?? []).length} học viên${filter === "active" ? " đang học" : ""}`}
        doodleColor="var(--pastel-pink-deep)"
        actions={
          <Button variant="primary" onClick={() => setShowAddForm((v) => !v)}>
            {showAddForm ? "Đóng" : "+ Thêm học viên"}
          </Button>
        }
      />

      {showAddForm && (
        <AddStudentForm
          onCreated={() => {
            setShowAddForm(false);
            refetch();
          }}
        />
      )}

      <div className={styles.toolbar}>
        <input
          className={styles.search}
          placeholder="Tìm theo tên học viên..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <div className={styles.tabs}>
          {(
            [
              { key: "active", label: "Đang học" },
              { key: "inactive", label: "Đã nghỉ" },
              { key: "all", label: "Tất cả" },
            ] as const
          ).map((tab) => (
            <button
              key={tab.key}
              className={`${styles.tab} ${filter === tab.key ? styles.tabActive : ""}`}
              onClick={() => setFilter(tab.key)}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <Card>
          <p style={{ color: "var(--danger)" }}>Không tải được danh sách học viên: {error}</p>
        </Card>
      )}

      {!error && loading && (
        <Card>
          <p style={{ color: "var(--ink-soft)" }}>Đang tải...</p>
        </Card>
      )}

      {!error && !loading && (students ?? []).length === 0 && (
        <Card>
          <div className={styles.empty}>Không tìm thấy học viên nào phù hợp. 🔍</div>
        </Card>
      )}

      {!error && !loading && (students ?? []).length > 0 && (
        <div className={styles.grid}>
          {(students ?? []).map((s, i) => (
            <Card key={s.id} className={styles.studentCard} onClick={() => toggleExpand(s.id)}>
              <div className={styles.studentTop}>
                <div className={styles.avatar} style={{ background: AVATAR_COLORS[i % AVATAR_COLORS.length] }}>
                  {initials(s.name)}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div className={styles.name}>{s.name}</div>
                  <div className={styles.meta}>{s.age !== null ? `${s.age} tuổi` : "Chưa rõ tuổi"}</div>
                </div>
                <Badge tone={s.status === "active" ? "success" : "neutral"}>
                  {s.status === "active" ? "Đang học" : "Đã nghỉ"}
                </Badge>
              </div>

              <div className={styles.price}>{formatVND(Number(s.price_per_session))} / buổi</div>

              {expandedId === s.id && (
                <div className={styles.detail} onClick={(e) => e.stopPropagation()}>
                  {detailLoading && <span>Đang tải chi tiết...</span>}
                  {detail && detail.id === s.id && editingId === s.id && (
                    <EditStudentForm
                      student={detail}
                      onSaved={async () => {
                        setEditingId(null);
                        await reloadDetail(s.id);
                        refetch();
                      }}
                      onCancel={() => setEditingId(null)}
                    />
                  )}
                  {detail && detail.id === s.id && editingId !== s.id && (
                    <>
                      <span>Học từ {new Date(detail.start_date).toLocaleDateString("vi-VN")}</span>
                      <span>Số buổi tính phí tháng này: {detail.sessions_this_month_count}</span>
                      {detail.note && <span>📝 {detail.note}</span>}
                      {detail.schedules.length > 0 && (
                        <div>
                          {detail.schedules.map((sc) => (
                            <span key={sc.id} className={styles.scheduleChip}>
                              {sc.day_of_week_display} {sc.start_time.slice(0, 5)}-{sc.end_time.slice(0, 5)}
                            </span>
                          ))}
                        </div>
                      )}
                      <div style={{ display: "flex", gap: 8, marginTop: 4 }}>
                        <Button size="sm" variant="soft" onClick={() => setEditingId(s.id)}>
                          Sửa thông tin
                        </Button>
                        {detail.status === "active" && (
                          <Button size="sm" variant="danger" onClick={() => handleDeactivate(s.id, detail.name)}>
                            Cho tạm nghỉ
                          </Button>
                        )}
                      </div>
                    </>
                  )}
                </div>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

function EditStudentForm({
  student,
  onSaved,
  onCancel,
}: {
  student: ApiStudentDetail;
  onSaved: () => void;
  onCancel: () => void;
}) {
  const [name, setName] = useState(student.name);
  const [startDate, setStartDate] = useState(student.start_date);
  const [dob, setDob] = useState(student.dob ?? "");
  const [note, setNote] = useState(student.note);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function save(confirm: boolean) {
    setSubmitting(true);
    setError(null);
    try {
      await updateStudent(student.id, {
        name,
        start_date: startDate,
        dob: dob || null,
        note,
        ...(confirm ? { confirm: true } : {}),
      });
      onSaved();
    } catch (err) {
      if (err instanceof ApiError && err.status === 409 && err.body && typeof err.body === "object") {
        const body = err.body as { requires_confirmation?: boolean; warning?: string };
        if (body.requires_confirmation) {
          if (window.confirm(body.warning ?? "Xác nhận thay đổi?")) {
            await save(true);
            return;
          }
          setSubmitting(false);
          return;
        }
      }
      if (err instanceof ApiError && err.body && typeof err.body === "object") {
        const firstError = Object.values(err.body as Record<string, unknown>)[0];
        setError(Array.isArray(firstError) ? String(firstError[0]) : err.message);
      } else {
        setError(err instanceof Error ? err.message : "Không lưu được thay đổi.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    save(false);
  }

  return (
    <form className={styles.editForm} onSubmit={handleSubmit}>
      {error && <div className={styles.error}>{error}</div>}

      <div className={styles.formField}>
        <label className={styles.formLabel}>Tên học viên *</label>
        <input className={styles.input} value={name} onChange={(e) => setName(e.target.value)} required />
      </div>
      <div className={styles.formField}>
        <label className={styles.formLabel}>Ngày bắt đầu học *</label>
        <input
          className={styles.input}
          type="date"
          value={startDate}
          onChange={(e) => setStartDate(e.target.value)}
          required
        />
      </div>
      <div className={styles.formField}>
        <label className={styles.formLabel}>Ngày sinh</label>
        <input className={styles.input} type="date" value={dob} onChange={(e) => setDob(e.target.value)} />
      </div>
      <div className={styles.formField}>
        <label className={styles.formLabel}>Giá / buổi</label>
        <input
          className={styles.input}
          value={`${Number(student.price_per_session).toLocaleString("vi-VN")} đ (không đổi được)`}
          disabled
        />
      </div>
      <div className={`${styles.formField} ${styles.wide}`}>
        <label className={styles.formLabel}>Ghi chú</label>
        <input className={styles.input} value={note} onChange={(e) => setNote(e.target.value)} />
      </div>

      <div className={styles.formActions}>
        <Button type="button" variant="ghost" size="sm" onClick={onCancel}>
          Hủy
        </Button>
        <Button type="submit" variant="primary" size="sm" disabled={submitting}>
          {submitting ? "Đang lưu..." : "Lưu thay đổi"}
        </Button>
      </div>
    </form>
  );
}

function AddStudentForm({ onCreated }: { onCreated: () => void }) {
  const [name, setName] = useState("");
  const [startDate, setStartDate] = useState(new Date().toISOString().slice(0, 10));
  const [price, setPrice] = useState("");
  const [dob, setDob] = useState("");
  const [note, setNote] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await createStudent({
        name,
        start_date: startDate,
        price_per_session: Number(price),
        dob: dob || null,
        note,
      });
      onCreated();
    } catch (err) {
      if (err instanceof ApiError && err.body && typeof err.body === "object") {
        const firstError = Object.values(err.body as Record<string, unknown>)[0];
        setError(Array.isArray(firstError) ? String(firstError[0]) : err.message);
      } else {
        setError(err instanceof Error ? err.message : "Không tạo được học viên.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Card tint="pink">
      <SectionHeading title="Thêm học viên mới" doodleColor="var(--pastel-pink-deep)" />
      <form className={styles.form} onSubmit={handleSubmit}>
        {error && <div className={styles.error}>{error}</div>}

        <div className={styles.formField}>
          <label className={styles.formLabel}>Tên học viên *</label>
          <input className={styles.input} value={name} onChange={(e) => setName(e.target.value)} required />
        </div>
        <div className={styles.formField}>
          <label className={styles.formLabel}>Giá / buổi (đ) *</label>
          <input
            className={styles.input}
            type="number"
            min={1}
            value={price}
            onChange={(e) => setPrice(e.target.value)}
            required
          />
        </div>
        <div className={styles.formField}>
          <label className={styles.formLabel}>Ngày bắt đầu học *</label>
          <input
            className={styles.input}
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            required
          />
        </div>
        <div className={styles.formField}>
          <label className={styles.formLabel}>Ngày sinh</label>
          <input className={styles.input} type="date" value={dob} onChange={(e) => setDob(e.target.value)} />
        </div>
        <div className={`${styles.formField} ${styles.wide}`}>
          <label className={styles.formLabel}>Ghi chú</label>
          <input className={styles.input} value={note} onChange={(e) => setNote(e.target.value)} />
        </div>

        <div className={styles.formActions}>
          <Button type="submit" variant="primary" disabled={submitting}>
            {submitting ? "Đang lưu..." : "Lưu học viên"}
          </Button>
        </div>
      </form>
    </Card>
  );
}
