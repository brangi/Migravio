interface LogoProps {
  size?: "sm" | "md" | "lg";
  variant?: "full" | "icon";
  colorScheme?: "light" | "dark";
  className?: string;
}

export function Logo({ size = "md", variant = "full", colorScheme = "light", className = "" }: LogoProps) {
  const dimensions = {
    sm: 24,
    md: 32,
    lg: 48,
  };

  const dim = dimensions[size];
  const textSize = {
    sm: "text-lg",
    md: "text-xl",
    lg: "text-2xl",
  };

  const isDark = colorScheme === "dark";

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      {/* Icon Mark: Two converging paths representing migration journey */}
      <svg
        width={dim}
        height={dim}
        viewBox="0 0 48 48"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
      >
        {/* Left path */}
        <path
          d="M8 40 Q12 32, 16 24 Q20 16, 24 8"
          stroke="currentColor"
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
          className={isDark ? "text-primary-200" : "text-primary-600"}
        />
        {/* Right path in amber accent */}
        <path
          d="M40 40 Q36 32, 32 24 Q28 16, 24 8"
          stroke="currentColor"
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="text-accent-500"
        />
        {/* Destination point at convergence */}
        <circle
          cx="24"
          cy="8"
          r="3.5"
          fill="currentColor"
          className="text-accent-500"
        />
      </svg>

      {/* Text */}
      {variant === "full" && (
        <span className={`font-display font-bold ${textSize[size]} ${isDark ? "text-white" : "text-primary-700"}`}>
          Migravio
        </span>
      )}
    </div>
  );
}
