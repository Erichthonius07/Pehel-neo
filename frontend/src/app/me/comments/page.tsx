"use client";
import { LayoutShell } from "@/components/layout/LayoutShell";
import { EmptyState } from "@/components/shared/EmptyState";

export default function MyCommentsPage() {
  return (
    <LayoutShell>
      <h1 className="text-4xl font-extrabold text-text-primary mb-2">MY COMMENTS</h1>
      <div className="chapter-break mb-6" />
      <EmptyState title="NO COMMENTS" message="You haven't commented on any issues yet." />
    </LayoutShell>
  );
}