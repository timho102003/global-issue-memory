import { type HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export interface AvatarProps extends HTMLAttributes<HTMLDivElement> {
  src?: string;
  alt?: string;
  fallback?: string;
  size?: "sm" | "default" | "lg";
}

/**
 * Avatar component matching GIM.pen design.
 */
function Avatar({ src, alt, fallback, size = "default", className, ...props }: AvatarProps) {
  const sizeClasses = {
    sm: "h-8 w-8 text-xs",
    default: "h-10 w-10 text-sm",
    lg: "h-16 w-16 text-lg",
  };

  return (
    <div
      className={cn(
        "relative flex shrink-0 items-center justify-center overflow-hidden rounded-full bg-gradient-to-br from-[#2D2A26] to-[#4A4A4A] ring-2 ring-white/60 shadow-sm",
        sizeClasses[size],
        className
      )}
      {...props}
    >
      {src ? (
        <img src={src} alt={alt || ""} className="h-full w-full object-cover" />
      ) : (
        <span className="font-medium text-white">
          {fallback || "?"}
        </span>
      )}
    </div>
  );
}

export { Avatar };
