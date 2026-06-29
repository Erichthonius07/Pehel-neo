"use client";
import { useEffect, useState } from "react";
import { LayoutShell } from "@/components/layout/LayoutShell";
import { meApi } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { CategoryLabel } from "@/components/shared/CategoryLabel";
import { StateBadge } from "@/components/shared/StateBadge";
import { EmptyState } from "@/components/shared/EmptyState";
import { formatDaysAgo } from "@/lib/utils";
import { MapPin } from "lucide-react";

export default function MyIssuesPage() {
  const { citizenToken } = useAuth();
  const [issues, setIssues] = useState<any[]>([]);

  useEffect(() => {
    if (!citizenToken) return;
    meApi.getIssues(citizenToken).then(setIssues);
  }, [citizenToken]);

  if (!citizenToken) return <LayoutShell><div className="p-12"><p>Please login</p></div></LayoutShell>;

  if (issues.length === 0) return (
    <LayoutShell>
      <h1 className="text-4xl font-extrabold text-text-primary mb-2">MY REPORTED ISSUES</h1>
      <div className="chapter-break mb-6" />
      <EmptyState title="NO REPORTED ISSUES" message="You haven't reported any issues yet." actionLabel="REPORT AN ISSUE" actionHref="/issues/new" />
    </LayoutShell>
  );

  return (
    <LayoutShell>
      <h1 className="text-4xl font-extrabold text-text-primary mb-2">MY REPORTED ISSUES</h1>
      <div className="chapter-break mb-6" />
      <p className="text-sm text-text-secondary mb-8">You have reported {issues.length} issues</p>
      
      <div className="grid grid-cols-3 gap-6">
        {issues.map((issue: any) => (
          <div key={issue.id} className="bg-white border border-border-light p-4">
            <div className="flex justify-between mb-2">
              <CategoryLabel category={issue.category} />
              <StateBadge state={issue.state} />
            </div>
            <h3 className="text-lg font-bold mb-2">{issue.title}</h3>
            <div className="flex items-center gap-1 text-xs text-text-secondary mb-2">
              <MapPin size={12} /> {issue.location_text}
            </div>
            <p className="text-xs text-text-muted">REPORTED {formatDaysAgo(issue.created_at)}</p>
          </div>
        ))}
      </div>
    </LayoutShell>
  );
}