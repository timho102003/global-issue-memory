import { forwardRef, type ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "secondary" | "ghost" | "outline" | "destructive";
  size?: "default" | "sm" | "lg" | "icon";
}

/**
 * Button component with variants matching GIM.pen design.
 */
const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", ...props }, ref) => {
    return (
      <button
        className={cn(
          "inline-flex items-center justify-center gap-2 whitespace-nowrap font-medium transition-colors",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
          "disabled:pointer-events-none disabled:opacity-50",
          // Variants
          {
            "bg-[#D4A853] text-white hover:bg-[#C49843]": variant === "default",
            "bg-secondary text-secondary-foreground hover:bg-secondary/80": variant === "secondary",
            "hover:bg-accent hover:text-accent-foreground": variant === "ghost",
            "border border-border bg-transparent hover:bg-accent hover:text-accent-foreground": variant === "outline",
            "bg-destructive text-white hover:bg-destructive/90": variant === "destructive",
          },
          // Sizes
          {
            "h-10 px-6 py-2 text-sm rounded-[24px]": size === "default",
            "h-8 px-4 text-xs rounded-[20px]": size === "sm",
            "h-12 px-8 py-4 text-base rounded-[24px]": size === "lg",
            "h-10 w-10 rounded-full": size === "icon",
          },
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export { Button };
