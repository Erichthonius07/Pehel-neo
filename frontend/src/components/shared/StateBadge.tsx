"use client";
import { STATE_BADGE_STYLES } from "@/lib/utils";

export function StateBadge({ state }: { state: string }) {
  const styles = STATE_BADGE_STYLES[state] || STATE_BADGE_STYLES['reported'];
  return (
    <span className="inline-block px-3 py-1 text-[10px] font-semibold uppercase tracking-wider"
      style={{ backgroundColor: styles.bg, color: styles.text, border: styles.border || 'none' }}>
      {state.replace(/_/g, ' ')}
    </span>
  );
}