"use client";

import { useEffect, useState } from "react";
import { LayoutShell } from "@/components/layout/LayoutShell";
import { feedApi, geoApi } from "@/lib/api";
import { CategoryLabel } from "@/components/shared/CategoryLabel";
import { StateBadge } from "@/components/shared/StateBadge";
import { PriorityIndicator } from "@/components/shared/PriorityIndicator";
import { formatDateTime, formatDaysAgo } from "@/lib/utils";
import { MapPin } from "lucide-react";

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
  sla_status?: string;
}

export default function DashboardPage() {
  const [issues, setIssues] = useState<Issue[]>([]);
  const [wards, setWards] = useState<{id: string; name: string}[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      feedApi.list(),
      geoApi.getCityWards("26484efc-20a0-4a15-8686-a724b161598d"),
    ]).then(([issuesRes, wardsRes]) => {
      setIssues(issuesRes as Issue[]);
      setWards(wardsRes as {id: string; name: string}[]);
      setLoading(false);
    });
  }, []);

  if (loading) return <LayoutShell><div className="p-12"><p className="mono-text">Loading...</p></div></LayoutShell>;

  const activeIssues = issues.filter(i => !['closed', 'resolved_confirmed'].includes(i.state)).length;
  const overdueIssues = issues.filter(i => i.sla_status === 'Overdue').length;

  return (
    <LayoutShell>
      <div className="mb-2">
        <p className="text-xs text-text-muted mb-1">KANPUR</p>
        <h1 className="text-5xl font-black tracking-tight text-text-primary">KANPUR <span className="text-border-medium mx-4">|</span> WARD 32 - SHANTI NAGAR</h1>
      </div>
      <p className="mono-text text-text-secondary mb-12">{new Date().toLocaleDateString('en-GB', {day:'2-digit',month:'short',year:'numeric'}).toUpperCase()}, {new Date().toLocaleTimeString('en-GB',{hour:'2-digit',minute:'2-digit',hour12:false})}</p>

      {/* Stat Cards */}
      <div className="flex mb-12 border-b border-border-light">
        {[
          { label: "ACTIVE ISSUES", value: activeIssues, link: "VIEW ALL ISSUES →" },
          { label: "SLA BREACHES", value: overdueIssues, link: "VIEW DETAILS →", color: overdueIssues > 0 ? '#C41E1E' : '#1A1A1A' },
          { label: "RESOLUTION RATE", value: "86.4%", link: "THIS MONTH" },
          { label: "AVG. RESOLUTION TIME", value: "4.2", suffix: "DAYS", link: "THIS MONTH" },
          { label: "OPEN REQUESTS", value: issues.filter(i => i.state === 'reported').length, link: "VIEW ALL REQUESTS →" },
          { label: "INSPECTIONS DUE", value: 17, link: "VIEW SCHEDULE →" },
        ].map((stat, i) => (
          <div key={i} className={`flex-1 py-6 px-4 ${i < 5 ? 'border-r border-border-light' : ''}`}>
            <p className="label-text mb-2">{stat.label}</p>
            <p className="text-4xl data-number text-text-primary mb-2" style={stat.color ? {color: stat.color} : {}}>
              {stat.value}{stat.suffix ? <span className="text-lg ml-1">{stat.suffix}</span> : null}
            </p>
            <p className="text-xs uppercase text-text-secondary hover:text-text-primary cursor-pointer">{stat.link}</p>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex gap-4 mb-12">
        <div className="flex gap-2">
          <span className="label-text mr-2 self-center">CATEGORY</span>
          {['ALL', 'WATER', 'GARBAGE', 'ROADS'].map(c => (
            <button key={c} className={`px-4 py-2 text-xs font-semibold uppercase border ${c === 'ALL' ? 'bg-text-primary text-white border-text-primary' : 'border-border-medium text-text-secondary hover:bg-surface-secondary'}`}>
              {c}
            </button>
          ))}
        </div>
        <div className="flex gap-2 ml-auto">
          <span className="label-text mr-2 self-center">STATUS</span>
          {['ALL', 'OPEN', 'IN PROGRESS', 'RESOLVED', 'CLOSED'].map(s => (
            <button key={s} className={`px-4 py-2 text-xs font-semibold uppercase border ${s === 'ALL' ? 'bg-text-primary text-white border-text-primary' : 'border-border-medium text-text-secondary hover:bg-surface-secondary'}`}>
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Timeline */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-text-primary mb-6 border-b-[3px] border-text-primary pb-2 inline-block">TIMELINE</h2>
        <div className="relative mt-8">
          <div className="h-1 bg-text-primary w-full absolute top-0" />
          <div className="flex justify-between relative pt-4">
            {issues.slice(0, 6).map((issue, i) => (
              <div key={issue.id} className={`w-[280px] ${i % 2 === 0 ? '-mt-32' : 'mt-8'}`}>
                <div className="bg-white border border-border-light p-4">
                  <div className="flex justify-between mb-2">
                    <CategoryLabel category={issue.category} />
                    <span className="mono-text text-text-secondary text-xs">#{issue.id.slice(0,8)}</span>
                  </div>
                  <h3 className="text-base font-bold text-text-primary mb-2">{issue.title}</h3>
                  <div className="flex items-center gap-1 text-text-secondary text-xs mb-2">
                    <MapPin size={12} /> {issue.location_text || "Unknown location"}
                  </div>
                  <div className="flex justify-between">
                    <PriorityIndicator priority={issue.severity} />
                    <span className="text-xs text-text-muted">{formatDaysAgo(issue.created_at)}</span>
                  </div>
                </div>
                <div className="w-2 h-2 bg-text-primary mx-auto mt-2" />
              </div>
            ))}
          </div>
        </div>
      </div>
    </LayoutShell>
  );
}