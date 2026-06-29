"use client";
import { Button } from "@/components/ui/button";

export function EmptyState({ title, message, actionLabel, actionHref }: { title: string; message: string; actionLabel?: string; actionHref?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <h3 className="text-2xl font-bold text-text-primary mb-2">{title}</h3>
      <div className="chapter-break w-48 mb-6" />
      <p className="text-sm text-text-secondary mb-8 whitespace-pre-line">{message}</p>
      {actionLabel && actionHref && (
        <a href={actionHref}><Button>{actionLabel}</Button></a>
      )}
    </div>
  );
}