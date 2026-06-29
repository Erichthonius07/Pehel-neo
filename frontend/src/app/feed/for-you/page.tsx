"use client";
import { LayoutShell } from "@/components/layout/LayoutShell";
import { EmptyState } from "@/components/shared/EmptyState";

export default function ForYouPage() {
  return (
    <LayoutShell>
      <h1 className="text-4xl font-extrabold text-text-primary mb-2">FOR YOU</h1>
      <div className="chapter-break mb-6" />
      <p className="text-sm text-text-secondary mb-8">Personalized for your ward and interests</p>
      <EmptyState title="COMING SOON" message="Personalized feed is being built." />
    </LayoutShell>
  );
}