import type { ReactNode } from "react";
import styles from "./StatTile.module.css";

interface StatTileProps {
  icon: ReactNode;
  iconBg: string;
  value: string | number;
  label: string;
}

export function StatTile({ icon, iconBg, value, label }: StatTileProps) {
  return (
    <div className={styles.tile}>
      <div className={styles.iconWrap} style={{ background: iconBg }}>
        {icon}
      </div>
      <div>
        <div className={styles.value}>{value}</div>
        <div className={styles.label}>{label}</div>
      </div>
    </div>
  );
}
