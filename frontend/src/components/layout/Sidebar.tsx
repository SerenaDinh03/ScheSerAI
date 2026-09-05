import { NavLink } from "react-router-dom";
import styles from "./Sidebar.module.css";
import { Doodle } from "../ui/Doodle";

const NAV_ITEMS = [
  { to: "/", label: "Tổng quan", icon: "sun", bg: "var(--pastel-yellow)", color: "#b8860b", end: true },
  { to: "/students", label: "Học viên", icon: "heart", bg: "var(--pastel-pink)", color: "var(--pastel-pink-deep)" },
  { to: "/schedule", label: "Lịch dạy", icon: "leaf", bg: "var(--mint-green)", color: "var(--mint-green-deep)" },
  { to: "/billing", label: "Học phí", icon: "sparkle", bg: "var(--lilac)", color: "var(--lilac-deep)" },
  { to: "/notifications", label: "Thông báo", icon: "wave", bg: "var(--powder-blue)", color: "var(--pastel-blue-deep)" },
] as const;

export function Sidebar() {
  return (
    <aside className={styles.sidebar}>
      <div className={styles.brand}>
        <div className={styles.brandMark}>🌸</div>
        <div>
          <div className={styles.brandName}>ScheSerAI</div>
          <div className={styles.brandSub}>Lịch dạy &amp; học phí</div>
        </div>
      </div>

      <nav className={styles.nav}>
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={"end" in item ? item.end : false}
            className={({ isActive }) => `${styles.link} ${isActive ? styles.linkActive : ""}`}
          >
            <span className={styles.iconWrap} style={{ background: item.bg }}>
              <Doodle kind={item.icon} color={item.color} size={16} />
            </span>
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className={styles.footer}>
        <Doodle kind="sparkle" color="var(--lilac-deep)" size={16} />
        Made with pastel &amp; chì màu 🎨
      </div>
    </aside>
  );
}
