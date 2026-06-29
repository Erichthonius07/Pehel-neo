"use client";

import { useEffect, useState } from "react";
import { LayoutShell } from "@/components/layout/LayoutShell";
import { feedApi } from "@/lib/api";
import { CategoryLabel } from "@/components/shared/CategoryLabel";
import { StateBadge } from "@/components/shared/StateBadge";
import { PriorityIndicator } from "@/components/shared/PriorityIndicator";
import { formatDaysAgo } from "@/lib/utils";
import { MapPin, Search } from "lucide-react";
import Link from "next/link";

interface Issue {
  id: string;
  title: string;
  category: string;
  state: string;
  severity: string;
  location_text: string;
  support_count: number;
  priority_score: number;
  created_at: string;
  geo_lat: number;
  geo_lng: number;
}

export default function IssuesPage() {
  const [issues, setIssues] = useState<Issue[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    feedApi.list().then((res) => {
      setIssues(res as Issue[]);
      setLoading(false);
    });
  }, []);

  const filtered = issues.filter((i) =>
    i.title.toLowerCase().includes(query.toLowerCase()) ||
    i.category.toLowerCase().includes(query.toLowerCase()) ||
    i.location_text?.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <LayoutShell>
      <h1 className="text-4xl font-extrabold text-text-primary mb-2">ALL ISSUES</h1>
      <div className="chapter-break mb-6" />
      <p className="text-sm text-text-secondary mb-8">
        {issues.length} issues reported across Kanpur
      </p>

      <div className="flex gap-4 mb-8">
        <div className="flex-1 flex items-center border-2 border-border-medium bg-surface-elevated">
          <Search size={16} className="ml-4 text-text-muted" />
          <input
            type="text"
            placeholder="SEARCH BY TITLE, CATEGORY, OR LOCATION..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="flex-1 h-12 px-4 bg-transparent text-sm focus:outline-none"
          />
        </div>
      </div>

      {loading ? (
        <p className="mono-text">Loading...</p>
      ) : (
        <div className="grid grid-cols-3 gap-6">
          {filtered.map((issue) => (
            <Link href={`/issues/${issue.id}`} key={issue.id}>
              <div className="bg-white border border-border-light p-4 hover:bg-surface-secondary transition-none h-full flex flex-col">
                <div className="flex justify-between mb-2">
                  <CategoryLabel category={issue.category} />
                  <StateBadge state={issue.state} />
                </div>
                <h3 className="text-lg font-bold text-text-primary mb-2 leading-tight">
                  {issue.title}
                </h3>
                <div className="flex items-center gap-1 text-xs text-text-secondary mb-3">
                  <MapPin size={12} />
                  {issue.location_text || "Unknown location"}
                </div>
                <div className="mt-auto flex justify-between items-center">
                  <PriorityIndicator priority={issue.severity} />
                  <span className="text-xs text-text-muted">
                    {formatDaysAgo(issue.created_at)}
                  </span>
                </div>
                <div className="hairline my-3" />
                <div className="flex justify-between text-xs text-text-secondary">
                  <span>SUPPORT: {issue.support_count}</span>
                  <span className="mono-text">#{issue.id.slice(0, 8)}</span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </LayoutShell>
  );
}