"use client";

import { useEffect, useState } from "react";
import { LayoutShell } from "@/components/layout/LayoutShell";
import { authorityApi, issuesApi } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { StateBadge } from "@/components/shared/StateBadge";
import { CategoryLabel } from "@/components/shared/CategoryLabel";
import { Button } from "@/components/ui/button";
import { formatDateTime } from "@/lib/utils";

interface QueueIssue {
  id: string;
  title: string;
  ward_id: string;
  category: string;
  created_at: string;
  state: string;
  sla_status: string;
}

export default function AuthorityPage() {
  const { authorityToken } = useAuth();
  const [issues, setIssues] = useState<QueueIssue[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!authorityToken) return;
    // Fetch all issues and filter by state for demo
    fetch('http://localhost:8000/api/v1/issues?limit=100')
      .then(r => r.json())
      .then(data => { setIssues(data as QueueIssue[]); setLoading(false); });
  }, [authorityToken]);

  if (!authorityToken) return <LayoutShell><div className="p-12"><p>Please login as authority</p></div></LayoutShell>;

  const newIssues = issues.filter(i => i.state === 'reported');
  const inProgress = issues.filter(i => i.state === 'in_progress');
  const overdue = issues.filter(i => i.sla_status === 'Overdue');

  const handleAction = async (issueId: string, action: string) => {
    if (!authorityToken) return;
    try {
      if (action === 'ack') await authorityApi.acknowledge(issueId, authorityToken);
      if (action === 'visit') await authorityApi.visit(issueId, authorityToken);
      if (action === 'start') await authorityApi.startWork(issueId, authorityToken);
      if (action === 'resolve') await authorityApi.resolve(issueId, authorityToken);
      alert(`${action} successful`);
    } catch (e) { alert('Action failed'); }
  };

  const QueueSection = ({ title, count, issues, actionLabel, actionType }: { title: string; count: number; issues: QueueIssue[]; actionLabel: string; actionType: string }) => (
    <div className="mb-16">
      <div className="relative mb-6">
        <div className="chapter-break" />
        <div className="absolute -top-3 left-0 bg-surface-pure pr-4">
          <h2 className="text-3xl font-extrabold text-text-primary inline">{title}</h2>
          <span className="text-sm text-text-secondary ml-4">{count} ISSUES</span>
        </div>
      </div>
      <table className="w-full">
        <thead>
          <tr className="border-b border-border-light">
            <th className="text-left label-text py-2">ISSUE TITLE</th>
            <th className="text-left label-text py-2">WARD</th>
            <th className="text-left label-text py-2">CATEGORY</th>
            <th className="text-left label-text py-2">REPORTED</th>
            <th className="text-left label-text py-2">STATE</th>
            <th className="text-left label-text py-2">ACTION</th>
          </tr>
        </thead>
        <tbody>
          {issues.map(issue => (
            <tr key={issue.id} className="border-b border-border-light hover:bg-surface-secondary">
              <td className="py-4 text-sm font-semibold text-text-primary">{issue.title}</td>
              <td className="py-4 text-sm text-text-secondary">32</td>
              <td className="py-4"><CategoryLabel category={issue.category} /></td>
              <td className="py-4 mono-text text-xs text-text-secondary">{formatDateTime(issue.created_at)}</td>
              <td className="py-4"><StateBadge state={issue.state} /></td>
              <td className="py-4">
                <Button variant="outline" size="sm" onClick={() => handleAction(issue.id, actionType)}>{actionLabel}</Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );

  return (
    <LayoutShell>
      <h1 className="text-4xl font-extrabold text-text-primary mb-2">AUTHORITY WORKSPACE</h1>
      <p className="text-base text-text-secondary mb-12">WARD 32 - SHANTI NAGAR</p>
      
      <QueueSection title="NEW" count={newIssues.length} issues={newIssues} actionLabel="ACKNOWLEDGE" actionType="ack" />
      <QueueSection title="DUE SOON" count={0} issues={[]} actionLabel="ESCALATE" actionType="escalate" />
      <QueueSection title="OVERDUE" count={overdue.length} issues={overdue} actionLabel="ESCALATE" actionType="escalate" />
      <QueueSection title="IN PROGRESS" count={inProgress.length} issues={inProgress} actionLabel="RESOLVE" actionType="resolve" />
    </LayoutShell>
  );
}