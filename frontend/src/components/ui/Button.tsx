import type { ButtonHTMLAttributes } from "react";
import styles from "./Button.module.css";

type Variant = "primary" | "soft" | "ghost" | "danger";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: "md" | "sm";
}

export function Button({ variant = "primary", size = "md", className = "", ...rest }: ButtonProps) {
  const sizeClass = size === "sm" ? styles.sm : "";
  return <button className={`${styles.btn} ${styles[variant]} ${sizeClass} ${className}`} {...rest} />;
}
