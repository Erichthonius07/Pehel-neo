import { Sidebar } from "./Sidebar";

export function LayoutShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen bg-surface-primary">
      <Sidebar />
      <main className="ml-[240px] flex-1 min-h-screen">
        <div className="max-w-[1440px] mx-auto px-8 py-12">
          {children}
        </div>
      </main>
    </div>
  );
}