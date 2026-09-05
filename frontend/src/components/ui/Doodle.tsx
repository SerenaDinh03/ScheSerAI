type DoodleKind = "sparkle" | "heart" | "leaf" | "sun" | "wave";

interface DoodleProps {
  kind: DoodleKind;
  color?: string;
  size?: number;
  className?: string;
  style?: React.CSSProperties;
}

/** Small hand-drawn-style decorative icons echoing the pastel reference sheet. */
export function Doodle({ kind, color = "currentColor", size = 22, className, style }: DoodleProps) {
  const common = {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    className,
    style,
    "aria-hidden": true,
  } as const;

  switch (kind) {
    case "sparkle":
      return (
        <svg {...common}>
          <path
            d="M12 2c.6 3.2 1.4 5 3 6.6 1.6 1.6 3.4 2.4 6.6 3-3.2.6-5 1.4-6.6 3-1.6 1.6-2.4 3.4-3 6.6-.6-3.2-1.4-5-3-6.6-1.6-1.6-3.4-2.4-6.6-3 3.2-.6 5-1.4 6.6-3 1.6-1.6 2.4-3.4 3-6.6Z"
            fill={color}
          />
        </svg>
      );
    case "heart":
      return (
        <svg {...common}>
          <path
            d="M12 20.5s-7.6-4.6-10-9.3C.5 8 2 4.7 5.3 4c2-.4 4 .5 5.2 2.3.6.9.9 1.3 1.5 1.3s.9-.4 1.5-1.3C14.7 4.5 16.7 3.6 18.7 4 22 4.7 23.5 8 22 11.2c-2.4 4.7-10 9.3-10 9.3Z"
            fill={color}
          />
        </svg>
      );
    case "leaf":
      return (
        <svg {...common}>
          <path
            d="M4 20c8-1 13-6 15-15-8 1-13 6-15 15Z"
            fill={color}
          />
          <path
            d="M5 19c4-3 7-7 9-13"
            stroke="rgba(74,59,92,0.35)"
            strokeWidth="1"
            strokeLinecap="round"
            fill="none"
          />
        </svg>
      );
    case "sun":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="5" fill={color} />
          {Array.from({ length: 8 }).map((_, i) => {
            const angle = (i * Math.PI) / 4;
            const x1 = 12 + Math.cos(angle) * 7.5;
            const y1 = 12 + Math.sin(angle) * 7.5;
            const x2 = 12 + Math.cos(angle) * 10.5;
            const y2 = 12 + Math.sin(angle) * 10.5;
            return (
              <line
                key={i}
                x1={x1}
                y1={y1}
                x2={x2}
                y2={y2}
                stroke={color}
                strokeWidth="1.6"
                strokeLinecap="round"
              />
            );
          })}
        </svg>
      );
    case "wave":
      return (
        <svg {...common}>
          <path
            d="M2 15c2-2.5 4-2.5 6 0s4 2.5 6 0 4-2.5 6 0 4 2.5 6 0"
            stroke={color}
            strokeWidth="2"
            strokeLinecap="round"
            fill="none"
          />
          <path
            d="M2 19c2-2.5 4-2.5 6 0s4 2.5 6 0 4-2.5 6 0 4 2.5 6 0"
            stroke={color}
            strokeWidth="2"
            strokeLinecap="round"
            fill="none"
            opacity="0.5"
          />
        </svg>
      );
    default:
      return null;
  }
}
