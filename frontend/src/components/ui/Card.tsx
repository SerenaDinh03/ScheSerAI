import type { PropsWithChildren } from "react";
import styles from "./Card.module.css";

type Tint = "pink" | "blue" | "lavender" | "mint" | "peach" | "none";

const tintClass: Record<Tint, string> = {
  pink: styles.tintPink,
  blue: styles.tintBlue,
  lavender: styles.tintLavender,
  mint: styles.tintMint,
  peach: styles.tintPeach,
  none: "",
};

interface CardProps {
  tint?: Tint;
  className?: string;
}

export function Card({ tint = "none", className = "", children }: PropsWithChildren<CardProps>) {
  return <div className={`${styles.card} ${tintClass[tint]} ${className}`}>{children}</div>;
}
