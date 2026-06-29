"use client";
import { CATEGORY_COLORS } from "@/lib/utils";

export function CategoryLabel({ category }: { category: string }) {
  const color = CATEGORY_COLORS[category.toLowerCase()] || '#1A1A1A';
  return <span className="text-xs font-bold uppercase tracking-wider" style={{ color }}>{category}</span>;
}
