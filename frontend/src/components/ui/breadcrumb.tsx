import { type HTMLAttributes, type ReactNode } from "react";
import { ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * Breadcrumb components matching GIM.pen design.
 */
const Breadcrumb = ({
  className,
  ...props
}: HTMLAttributes<HTMLElement>) => (
  <nav
    aria-label="breadcrumb"
    className={cn("flex items-center gap-2 text-sm", className)}
    {...props}
  />
);

const BreadcrumbList = ({
  className,
  ...props
}: HTMLAttributes<HTMLOListElement>) => (
  <ol
    className={cn("flex items-center gap-2", className)}
    {...props}
  />
);

const BreadcrumbItem = ({
  className,
  ...props
}: HTMLAttributes<HTMLLIElement>) => (
  <li
    className={cn("flex items-center gap-2", className)}
    {...props}
  />
);

const BreadcrumbLink = ({
  className,
  isCurrentPage,
  ...props
}: HTMLAttributes<HTMLAnchorElement> & { isCurrentPage?: boolean; href?: string }) => (
  <a
    className={cn(
      "transition-colors",
      isCurrentPage
        ? "font-medium text-text-primary"
        : "text-text-muted hover:text-text-primary",
      className
    )}
    aria-current={isCurrentPage ? "page" : undefined}
    {...props}
  />
);

const BreadcrumbSeparator = ({
  children,
  className,
  ...props
}: HTMLAttributes<HTMLSpanElement> & { children?: ReactNode }) => (
  <span
    role="presentation"
    aria-hidden="true"
    className={cn("text-text-muted", className)}
    {...props}
  >
    {children || <ChevronRight className="h-4 w-4" />}
  </span>
);

const BreadcrumbPage = ({
  className,
  ...props
}: HTMLAttributes<HTMLSpanElement>) => (
  <span
    role="link"
    aria-disabled="true"
    aria-current="page"
    className={cn("font-medium text-text-primary", className)}
    {...props}
  />
);

export {
  Breadcrumb,
  BreadcrumbList,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbSeparator,
  BreadcrumbPage,
};
