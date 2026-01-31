interface DocsStepProps {
  number: string;
  title: string;
}

export function DocsStep({ number, title }: DocsStepProps) {
  return (
    <div className="mb-4 flex items-center gap-3">
      <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent-warm/10 text-[13px] font-bold text-accent-warm">
        {number}
      </span>
      <h2 className="text-xl font-semibold text-text-primary sm:text-2xl">
        {title}
      </h2>
    </div>
  );
}
