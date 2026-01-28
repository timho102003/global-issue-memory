"use client";

import { forwardRef, type InputHTMLAttributes } from "react";
import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

export interface CheckboxProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "type"> {}

/**
 * Checkbox component matching GIM.pen design.
 */
const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(
  ({ className, checked, ...props }, ref) => {
    return (
      <div className="relative inline-flex items-center">
        <input
          type="checkbox"
          ref={ref}
          checked={checked}
          className="peer sr-only"
          {...props}
        />
        <div
          className={cn(
            "h-5 w-5 shrink-0 rounded-md border transition-colors",
            "peer-focus-visible:ring-2 peer-focus-visible:ring-ring peer-focus-visible:ring-offset-2",
            "peer-disabled:cursor-not-allowed peer-disabled:opacity-50",
            checked
              ? "border-[#3D3D3D] bg-[#3D3D3D]"
              : "border-border bg-white",
            className
          )}
        >
          {checked && (
            <Check className="h-full w-full p-0.5 text-white" strokeWidth={3} />
          )}
        </div>
      </div>
    );
  }
);
Checkbox.displayName = "Checkbox";

export { Checkbox };
