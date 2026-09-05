import { useMemo, useState } from "react";
import styles from "./Students.module.css";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { SectionHeading } from "../components/ui/SectionHeading";
import { students } from "../data/mockData";
import type { Student, StudentStatus } from "../types";

const AVATAR_COLORS = ["var(--pastel-pink)", "var(--mint-green)", "var(--powder-blue)", "var(--lilac)", "var(--peach)"];

function initials(name: string) {
  const parts = name.trim().split(/\s+/);
  return parts[parts.length - 1]?.[0]?.toUpperCase() ?? "?";
}

function age(dob: string | null): number | null {
  if (!dob) return null;
  const birth = new Date(dob);
  const today = new Date();
  let years = today.getFullYear() - birth.getFullYear();
  const hadBirthday =
    today.getMonth() > birth.getMonth() ||
    (today.getMonth() === birth.getMonth() && today.getDate() >= birth.getDate());
  if (!hadBirthday) years -= 1;
  return years;
}

function formatVND(amount: number) {
  return amount.toLocaleString("vi-VN") + " đ";
}

type Filter = "all" | StudentStatus;

export function Students() {
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<Filter>("active");

  const filtered = useMemo(() => {
    return students.filter((s) => {
      const matchesStatus = filter === "all" ? true : s.status === filter;
      const matchesQuery = s.name.toLowerCase().includes(query.trim().toLowerCase());
      return matchesStatus && matchesQuery;
    });
  }, [query, filter]);

  return (
    <div className={styles.page}>
      <SectionHeading
        title="Học viên"
        subtitle={`${students.filter((s) => s.status === "active").length} học viên đang học`}
        doodleColor="var(--pastel-pink-deep)"
        actions={<Button variant="primary">+ Thêm học viên</Button>}
      />

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

      {filtered.length === 0 ? (
        <Card>
          <div className={styles.empty}>Không tìm thấy học viên nào phù hợp. 🔍</div>
        </Card>
      ) : (
        <div className={styles.grid}>
          {filtered.map((s: Student, i: number) => (
            <Card key={s.id} className={styles.studentCard}>
              <div className={styles.studentTop}>
                <div className={styles.avatar} style={{ background: AVATAR_COLORS[i % AVATAR_COLORS.length] }}>
                  {initials(s.name)}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div className={styles.name}>{s.name}</div>
                  <div className={styles.meta}>
                    {age(s.dob) !== null ? `${age(s.dob)} tuổi · ` : ""}
                    Học từ {new Date(s.startDate).toLocaleDateString("vi-VN")}
                  </div>
                </div>
                <Badge tone={s.status === "active" ? "success" : "neutral"}>
                  {s.status === "active" ? "Đang học" : "Đã nghỉ"}
                </Badge>
              </div>

              <div className={styles.price}>{formatVND(s.pricePerSession)} / buổi</div>

              {s.note && <div className={styles.note}>📝 {s.note}</div>}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
