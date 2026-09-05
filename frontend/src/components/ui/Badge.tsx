import type { PropsWithChildren } from "react";
import styles from "./Badge.module.css";

type Tone = "success" | "warning" | "danger" | "info" | "neutral";

interface BadgeProps {
  tone?: Tone;
  dot?: boolean;
  className?: string;
}

export function Badge({ tone = "neutral", dot = false, className = "", children }: PropsWithChildren<BadgeProps>) {
  return (
    <span className={`${styles.badge} ${styles[tone]} ${className}`}>
      {dot && <span className={styles.dot} />}
      {children}
    </span>
  );
}
