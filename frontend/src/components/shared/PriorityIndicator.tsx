"use client";
import { PRIORITY_STYLES } from "@/lib/utils";

export function PriorityIndicator({ priority }: { priority: string }) {
  const style = PRIORITY_STYLES[priority.toLowerCase()] || PRIORITY_STYLES['medium'];
  return (
    <div className="flex items-center gap-2">
      <span className="label-text">PRIORITY</span>
      <span className="text-sm font-bold uppercase" style={{ color: style.color, fontWeight: style.weight }}>{priority}</span>
    </div>
  );
}