import type { ReactNode } from "react";
import styles from "./SectionHeading.module.css";
import { Doodle } from "./Doodle";

interface SectionHeadingProps {
  title: string;
  subtitle?: string;
  doodleColor?: string;
  actions?: ReactNode;
}

export function SectionHeading({ title, subtitle, doodleColor = "var(--lilac-deep)", actions }: SectionHeadingProps) {
  return (
    <div className={styles.wrap}>
      <div className={styles.top}>
        <h2 className={styles.title}>
          <Doodle kind="sparkle" color={doodleColor} size={20} />
          {title}
        </h2>
        {actions && <div className={styles.actions}>{actions}</div>}
      </div>
      {subtitle && <p className={styles.subtitle}>{subtitle}</p>}
      <hr className="dashedDivider" />
    </div>
  );
}
