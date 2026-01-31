import Image from "next/image";
import { cn } from "@/lib/utils";

interface DocsImageProps {
  src: string;
  alt: string;
  width: number;
  height: number;
  className?: string;
  centered?: boolean;
  maxWidth?: string;
}

export function DocsImage({
  src,
  alt,
  width,
  height,
  className,
  centered = false,
  maxWidth,
}: DocsImageProps) {
  const wrapper = (
    <div
      className={cn(
        "overflow-hidden rounded-xl border border-border-light shadow-[var(--shadow-card)]",
        className
      )}
    >
      <Image src={src} alt={alt} width={width} height={height} className="w-full" />
    </div>
  );

  if (centered || maxWidth) {
    return (
      <div className={cn("mx-auto", maxWidth ?? "max-w-[520px]")}>
        {wrapper}
      </div>
    );
  }

  return wrapper;
}
