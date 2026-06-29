"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { LayoutShell } from "@/components/layout/LayoutShell";
import { issuesApi, chatApi } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { CategoryLabel } from "@/components/shared/CategoryLabel";
import { StateBadge } from "@/components/shared/StateBadge";
import { PriorityIndicator } from "@/components/shared/PriorityIndicator";
import { ActorBadge } from "@/components/shared/ActorBadge";
import { Button } from "@/components/ui/button";
import { formatDateTime, formatDaysAgo, getColor } from "@/lib/utils";
import { MapPin, MessageSquare, Heart, CheckCircle, AlertTriangle, ArrowLeft } from "lucide-react";
import Link from "next/link";

interface TimelineEvent {
  id: string;
  event_type: string;
  created_at: string;
  actor_type: string;
  actor_name?: string;
  message?: string;
}

interface Comment {
  id: string;
  message_text: string;
  created_at: string;
  actor_type: string;
  authority_user_name?: string;
}

interface IssueDetail {
  id: string;
  title: string;
  description: string;
  category: string;
  state: string;
  severity: string;
  location_text: string;
  geo_lat: number;
  geo_lng: number;
  support_count: number;
  priority_score: number;
  created_at: string;
  sla_status?: string;
  ward_id?: string;
  ai_summary?: string;
  reporter_id?: string;
}

export default function IssueDetailClient({ id }: { id: string }) {
  const router = useRouter();
  const { citizenToken, isCitizen } = useAuth();

  const [issue, setIssue] = useState<IssueDetail | null>(null);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [comments, setComments] = useState<Comment[]>([]);
  const [newComment, setNewComment] = useState("");
  const [loading, setLoading] = useState(true);
  const [chatQuestion, setChatQuestion] = useState("");
  const [chatAnswer, setChatAnswer] = useState("");

  useEffect(() => {
    Promise.all([
      issuesApi.get(id),
      issuesApi.getTimeline(id),
      issuesApi.getComments(id),
    ]).then(([issueRes, timelineRes, commentsRes]) => {
      setIssue(issueRes as IssueDetail);
      setTimeline(timelineRes as TimelineEvent[]);
      setComments(commentsRes as Comment[]);
      setLoading(false);
    });
  }, [id]);

  const handleSupport = async () => {
    if (!citizenToken) return;
    try {
      await issuesApi.support(id, citizenToken);
      alert("Supported!");
      if (issue) setIssue({ ...issue, support_count: issue.support_count + 1 });
    } catch (e) {
      alert("Already supported or own issue");
    }
  };

  const handleComment = async () => {
    if (!citizenToken || !newComment.trim()) return;
    try {
      await issuesApi.addComment(id, newComment, citizenToken);
      setNewComment("");
      const refreshed = await issuesApi.getComments(id);
      setComments(refreshed as Comment[]);
    } catch (e) {
      alert("Failed to post comment");
    }
  };

  const handleConfirm = async () => {
    if (!citizenToken) return;
    try {
      await issuesApi.confirm(id, citizenToken);
      alert("Resolution confirmed!");
      router.refresh();
    } catch (e) {
      alert("Cannot confirm");
    }
  };

  const handleDispute = async () => {
    if (!citizenToken) return;
    try {
      await issuesApi.dispute(id, citizenToken);
      alert("Resolution disputed!");
      router.refresh();
    } catch (e) {
      alert("Cannot dispute");
    }
  };

  const handleChat = async () => {
    if (!citizenToken || !chatQuestion.trim()) return;
    try {
      const res = await chatApi.ask(id, chatQuestion, citizenToken);
      setChatAnswer((res as any).answer || "No response");
    } catch (e) {
      alert("Chat failed");
    }
  };

  if (loading || !issue) {
    return (
      <LayoutShell>
        <div className="p-12">
          <p className="mono-text">Loading issue...</p>
        </div>
      </LayoutShell>
    );
  }

  const isResolvedClaimed = issue.state === "resolved_claimed";
  const canConfirmOrDispute = isCitizen && isResolvedClaimed;

  return (
    <LayoutShell>
      <Link href="/issues" className="text-xs uppercase text-text-secondary hover:text-text-primary mb-4 inline-flex items-center gap-2">
        <ArrowLeft size={14} /> BACK TO ISSUES
      </Link>

      <div className="mb-8">
        <div className="flex items-center gap-4 mb-4">
          <CategoryLabel category={issue.category} />
          <StateBadge state={issue.state} />
          <PriorityIndicator priority={issue.severity} />
        </div>
        <h1 className="text-5xl font-black tracking-tight text-text-primary mb-4">
          {issue.title}
        </h1>
        <div className="flex items-center gap-6 text-sm text-text-secondary">
          <span className="mono-text">#{issue.id.slice(0, 8)}</span>
          <span className="flex items-center gap-1">
            <MapPin size={14} /> {issue.location_text}
          </span>
          <span>{formatDaysAgo(issue.created_at)}</span>
          <span className="mono-text">SUPPORT: {issue.support_count}</span>
        </div>
      </div>

      <div className="chapter-break mb-8" />

      <div className="grid grid-cols-[1fr_360px] gap-12">
        <div>
          <div className="mb-12">
            <h2 className="text-2xl font-bold text-text-primary mb-4 border-b-[3px] border-text-primary pb-2 inline-block">
              DESCRIPTION
            </h2>
            <p className="text-base text-text-secondary leading-relaxed whitespace-pre-line">
              {issue.description}
            </p>
          </div>

          {issue.ai_summary && (
            <div className="mb-12 border border-border-light p-6 bg-surface-elevated">
              <p className="label-text mb-2">AI SUMMARY</p>
              <p className="text-sm text-text-secondary italic">{issue.ai_summary}</p>
            </div>
          )}

          <div className="mb-12">
            <h2 className="text-2xl font-bold text-text-primary mb-6 border-b-[3px] border-text-primary pb-2 inline-block">
              TIMELINE
            </h2>
            <div className="border-l-2 border-border-heavy pl-6 space-y-6">
              {timeline.map((event) => (
                <div key={event.id} className="relative">
                  <div className="absolute -left-[31px] top-0 w-4 h-4 bg-text-primary border-2 border-surface-primary" />
                  <div className="flex items-center gap-3 mb-1">
                    <ActorBadge actor={event.actor_type} />
                    <span className="text-xs text-text-muted">
                      {formatDateTime(event.created_at)}
                    </span>
                  </div>
                  <p className="text-sm font-semibold text-text-primary uppercase">
                    {event.event_type.replace(/_/g, " ")}
                  </p>
                  {event.message && (
                    <p className="text-sm text-text-secondary mt-1">{event.message}</p>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="mb-12">
            <h2 className="text-2xl font-bold text-text-primary mb-6 border-b-[3px] border-text-primary pb-2 inline-block">
              COMMENTS
            </h2>
            {comments.length === 0 && (
              <p className="text-sm text-text-secondary mb-4">No comments yet.</p>
            )}
            <div className="space-y-4 mb-6">
              {comments.map((comment) => (
                <div key={comment.id} className="border border-border-light p-4 bg-white">
                  <div className="flex items-center gap-3 mb-2">
                    <ActorBadge actor={comment.actor_type} />
                    <span className="text-xs text-text-muted">
                      {formatDateTime(comment.created_at)}
                    </span>
                  </div>
                  <p className="text-sm text-text-primary">{comment.message_text}</p>
                </div>
              ))}
            </div>
            {isCitizen && (
              <div className="flex gap-2">
                <input
                  type="text"
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                  placeholder="Add a comment..."
                  className="flex-1 h-12 px-4 border-2 border-border-medium bg-surface-elevated text-sm focus:border-text-primary outline-none"
                />
                <Button onClick={handleComment} size="icon">
                  <MessageSquare size={16} />
                </Button>
              </div>
            )}
          </div>

          <div className="mb-12 border border-border-light p-6 bg-surface-elevated">
            <h2 className="text-xl font-bold text-text-primary mb-4">ASK ABOUT THIS ISSUE</h2>
            <div className="flex gap-2 mb-4">
              <input
                type="text"
                value={chatQuestion}
                onChange={(e) => setChatQuestion(e.target.value)}
                placeholder="What is the status?"
                className="flex-1 h-12 px-4 border-2 border-border-medium bg-white text-sm focus:border-text-primary outline-none"
              />
              <Button onClick={handleChat} disabled={!isCitizen}>
                ASK
              </Button>
            </div>
            {chatAnswer && (
              <div className="border border-border-medium p-4 bg-white">
                <p className="text-sm text-text-secondary">{chatAnswer}</p>
              </div>
            )}
          </div>
        </div>

        <div>
          <div className="sticky top-12 border border-border-light bg-white">
            <div className="p-6 border-b border-border-light">
              <p className="label-text mb-2">PRIORITY SCORE</p>
              <p
                className="text-5xl data-number"
                style={{ color: getColor(issue.priority_score, "percentage") }}
              >
                {issue.priority_score}
              </p>
            </div>

            <div className="p-6 border-b border-border-light">
              <p className="label-text mb-2">SLA STATUS</p>
              <p className="text-sm font-bold uppercase text-text-primary">
                {issue.sla_status || "ON TRACK"}
              </p>
            </div>

            <div className="p-6 space-y-3">
              {isCitizen && (
                <Button onClick={handleSupport} variant="outline" className="w-full">
                  <Heart size={16} className="mr-2" /> SUPPORT THIS ISSUE
                </Button>
              )}

              {canConfirmOrDispute && (
                <>
                  <div className="hairline" />
                  <p className="label-text text-center">RESOLUTION VERIFICATION</p>
                  <Button onClick={handleConfirm} className="w-full">
                    <CheckCircle size={16} className="mr-2" /> CONFIRM RESOLVED
                  </Button>
                  <Button onClick={handleDispute} variant="danger" className="w-full">
                    <AlertTriangle size={16} className="mr-2" /> DISPUTE RESOLUTION
                  </Button>
                </>
              )}

              <div className="hairline" />
              <Link href={`/chat/issue/${issue.id}`}>
                <Button variant="ghost" className="w-full">
                  OPEN FULL CHAT →
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </LayoutShell>
  );
}