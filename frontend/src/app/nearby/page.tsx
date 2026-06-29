"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { LayoutShell } from "@/components/layout/LayoutShell";
import { feedApi } from "@/lib/api";
import { CategoryLabel } from "@/components/shared/CategoryLabel";
import { PriorityIndicator } from "@/components/shared/PriorityIndicator";
import { formatDaysAgo } from "@/lib/utils";
import { MapPin } from "lucide-react";

const NearbyMap = dynamic(() => import("@/components/search/NearbyMap"), {
  ssr: false
});

export default function NearbyPage() {
  const [issues, setIssues] = useState<any[]>([]);
  const [radius, setRadius] = useState(1000);
  const [selectedIssue, setSelectedIssue] = useState<string | null>(null);

  const handleSearch = async () => {
    const res = await feedApi.nearby(26.4499, 80.3319, radius);
    setIssues(res as any[]);
  };

  return (
    <LayoutShell>
      <h1 className="text-4xl font-extrabold text-text-primary mb-2">ISSUES NEAR YOU</h1>
      <div className="chapter-break mb-6" />
      <p className="text-sm text-text-secondary mb-8">Showing issues within {radius / 1000} km</p>

      <div className="flex gap-4 mb-6">
        {[500, 1000, 2000, 5000].map(r => (
          <button key={r} onClick={() => { setRadius(r); handleSearch(); }}
            className={`px-4 py-2 text-xs font-semibold uppercase border ${radius === r ? 'bg-text-primary text-white' : 'border-border-medium text-text-secondary'}`}>
            {r / 1000}km
          </button>
        ))}
      </div>

      <div className="grid grid-cols-[40%_60%] gap-0 h-[600px]">
        <div className="overflow-y-auto border-r border-border-light pr-4">
          {issues.map((issue: any) => (
            <div key={issue.id} onClick={() => setSelectedIssue(issue.id)}
              className={`border border-border-light p-4 mb-2 cursor-pointer hover:bg-surface-secondary ${selectedIssue === issue.id ? 'bg-surface-secondary' : ''}`}>
              <p className="mono-text text-xs text-text-secondary mb-1">{issue.distance ? `${Math.round(issue.distance)}m away` : 'Nearby'}</p>
              <div className="flex justify-between mb-1">
                <CategoryLabel category={issue.category} />
                <span className="mono-text text-xs text-text-secondary">#{issue.id?.slice(0,8)}</span>
              </div>
              <h3 className="text-base font-bold mb-1">{issue.title}</h3>
              <div className="flex items-center gap-1 text-xs text-text-secondary mb-2">
                <MapPin size={12} /> {issue.location_text}
              </div>
              <PriorityIndicator priority={issue.severity} />
              <span className="text-xs text-text-muted ml-4">{formatDaysAgo(issue.created_at)}</span>
            </div>
          ))}
        </div>
        <div className="h-full">
          <NearbyMap issues={issues} selectedId={selectedIssue} onSelect={setSelectedIssue} />
        </div>
      </div>
    </LayoutShell>
  );
}
