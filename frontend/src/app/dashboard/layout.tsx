import { DashboardNav } from "@/components/layout/dashboard-nav";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen flex-col bg-gradient-to-b from-bg-gradient-start to-bg-gradient-end">
      <DashboardNav />
      {children}
    </div>
  );
}
