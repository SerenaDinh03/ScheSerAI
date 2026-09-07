import type { HTMLAttributes } from "react";
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

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  tint?: Tint;
}

export function Card({ tint = "none", className = "", ...rest }: CardProps) {
  return <div className={`${styles.card} ${tintClass[tint]} ${className}`} {...rest} />;
}
