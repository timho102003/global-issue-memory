import { DashboardNav } from "@/components/layout/dashboard-nav";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen flex-col bg-gradient-to-b from-bg-gradient-start to-bg-gradient-end">
      <DashboardNav />
      <div className="mx-auto flex w-full max-w-[1040px] flex-1 flex-col px-4 sm:px-6">
        {children}
      </div>
    </div>
  );
}
