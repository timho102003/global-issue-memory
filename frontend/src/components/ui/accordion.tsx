"use client";

import { createContext, useContext, useState, type ReactNode, type HTMLAttributes } from "react";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

interface AccordionContextValue {
  openItems: string[];
  toggleItem: (value: string) => void;
  type: "single" | "multiple";
}

const AccordionContext = createContext<AccordionContextValue | null>(null);

function useAccordion() {
  const context = useContext(AccordionContext);
  if (!context) throw new Error("useAccordion must be used within Accordion");
  return context;
}

interface AccordionProps {
  type?: "single" | "multiple";
  defaultValue?: string[];
  children: ReactNode;
  className?: string;
}

/**
 * Accordion component matching GIM.pen design.
 */
function Accordion({
  type = "single",
  defaultValue = [],
  children,
  className,
}: AccordionProps) {
  const [openItems, setOpenItems] = useState<string[]>(defaultValue);

  const toggleItem = (value: string) => {
    if (type === "single") {
      setOpenItems((prev) => (prev.includes(value) ? [] : [value]));
    } else {
      setOpenItems((prev) =>
        prev.includes(value)
          ? prev.filter((item) => item !== value)
          : [...prev, value]
      );
    }
  };

  return (
    <AccordionContext.Provider value={{ openItems, toggleItem, type }}>
      <div className={cn("flex flex-col gap-4", className)}>{children}</div>
    </AccordionContext.Provider>
  );
}

interface AccordionItemProps extends HTMLAttributes<HTMLDivElement> {
  value: string;
}

const AccordionItem = ({ value, className, children, ...props }: AccordionItemProps) => {
  const { openItems } = useAccordion();
  const isOpen = openItems.includes(value);

  return (
    <div
      data-state={isOpen ? "open" : "closed"}
      className={cn(
        "rounded-2xl border border-border-light/80 bg-white p-5 shadow-[var(--shadow-card)] transition-shadow duration-200 hover:shadow-[var(--shadow-card-hover)] sm:p-6",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

interface AccordionTriggerProps extends HTMLAttributes<HTMLButtonElement> {
  value: string;
}

const AccordionTrigger = ({
  value,
  className,
  children,
  ...props
}: AccordionTriggerProps) => {
  const { openItems, toggleItem } = useAccordion();
  const isOpen = openItems.includes(value);

  return (
    <button
      type="button"
      onClick={() => toggleItem(value)}
      className={cn(
        "flex w-full items-center justify-between text-left text-[14px] font-medium text-text-primary sm:text-[15px]",
        className
      )}
      {...props}
    >
      {children}
      <ChevronDown
        className={cn(
          "h-5 w-5 text-muted-foreground transition-transform duration-200",
          isOpen && "rotate-180"
        )}
      />
    </button>
  );
};

interface AccordionContentProps extends HTMLAttributes<HTMLDivElement> {
  value: string;
}

const AccordionContent = ({
  value,
  className,
  children,
  ...props
}: AccordionContentProps) => {
  const { openItems } = useAccordion();
  const isOpen = openItems.includes(value);

  if (!isOpen) return null;

  return (
    <div className={cn("mt-4 text-[13px] leading-relaxed text-text-secondary sm:text-[14px]", className)} {...props}>
      {children}
    </div>
  );
};

export { Accordion, AccordionItem, AccordionTrigger, AccordionContent };
