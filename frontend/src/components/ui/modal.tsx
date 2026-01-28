"use client";

import { useEffect, type HTMLAttributes, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

export interface ModalProps {
  open: boolean;
  onClose: () => void;
  children: ReactNode;
  className?: string;
}

/**
 * Modal component matching GIM.pen design (center variant).
 */
function Modal({ open, onClose, children, className }: ModalProps) {
  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };

    if (open) {
      document.addEventListener("keydown", handleEscape);
      document.body.style.overflow = "hidden";
    }

    return () => {
      document.removeEventListener("keydown", handleEscape);
      document.body.style.overflow = "";
    };
  }, [open, onClose]);

  if (!open) return null;

  return createPortal(
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      role="dialog"
      aria-modal="true"
    >
      {/* Overlay */}
      <div
        className="absolute inset-0 bg-black/40"
        onClick={onClose}
        aria-hidden="true"
      />
      {/* Content */}
      <div
        className={cn(
          "relative z-10 w-full max-w-[400px] rounded-[24px] bg-white p-8",
          className
        )}
      >
        {children}
      </div>
    </div>,
    document.body
  );
}

const ModalHeader = ({
  className,
  children,
  onClose,
  ...props
}: HTMLAttributes<HTMLDivElement> & { onClose?: () => void }) => (
  <div className={cn("flex items-center justify-between gap-3 mb-6", className)} {...props}>
    {children}
    {onClose && (
      <button
        onClick={onClose}
        className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted"
      >
        <X className="h-5 w-5" />
      </button>
    )}
  </div>
);

const ModalTitle = ({
  className,
  ...props
}: HTMLAttributes<HTMLHeadingElement>) => (
  <h2
    className={cn("text-xl font-semibold text-text-primary", className)}
    {...props}
  />
);

const ModalDescription = ({
  className,
  ...props
}: HTMLAttributes<HTMLParagraphElement>) => (
  <p className={cn("text-sm text-text-secondary", className)} {...props} />
);

const ModalContent = ({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("flex flex-col gap-6", className)} {...props} />
);

const ModalFooter = ({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("flex flex-col gap-3 mt-6", className)} {...props} />
);

export { Modal, ModalHeader, ModalTitle, ModalDescription, ModalContent, ModalFooter };
