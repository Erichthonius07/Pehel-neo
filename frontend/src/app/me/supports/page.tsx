"use client";
import { LayoutShell } from "@/components/layout/LayoutShell";
import { EmptyState } from "@/components/shared/EmptyState";

export default function MySupportsPage() {
  return (
    <LayoutShell>
      <h1 className="text-4xl font-extrabold text-text-primary mb-2">ISSUES I SUPPORT</h1>
      <div className="chapter-break mb-6" />
      <EmptyState title="NO SUPPORTS" message="You haven't supported any issues yet." />
    </LayoutShell>
  );
}