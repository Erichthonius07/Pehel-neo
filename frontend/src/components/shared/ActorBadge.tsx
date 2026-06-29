"use client";
import { ACTOR_BADGES } from "@/lib/utils";

export function ActorBadge({ actor }: { actor: string }) {
  const badge = ACTOR_BADGES[actor.toLowerCase()] || ACTOR_BADGES['system'];
  return (
    <span className="inline-block px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider"
      style={{ backgroundColor: badge.bg, color: badge.text }}>
      {badge.label}
    </span>
  );
}