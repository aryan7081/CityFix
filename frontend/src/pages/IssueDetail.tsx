import { FormEvent, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { PriorityBadge, StatusBadge } from "../components/StatusBadge";
import { useToast } from "../components/Toast";
import type { Issue, Team } from "../types";

export function IssueDetail() {
  const { publicId } = useParams();
  const { user } = useAuth();
  const { push } = useToast();
  const [issue, setIssue] = useState<Issue | null>(null);
  const [teams, setTeams] = useState<Team[]>([]);
  const [teamId, setTeamId] = useState("");
  const [comment, setComment] = useState("");
  const [resolveNotes, setResolveNotes] = useState("");
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const { data } = await api.get(`/issues/${publicId}/`);
      setIssue(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
    if (user?.role === "ADMIN") {
      api.get("/teams/").then((res) => {
        const list = res.data.results ?? res.data;
        setTeams(list);
        if (list[0]) setTeamId(String(list[0].id));
      });
    }
  }, [publicId, user?.role]);

  if (loading) return <div className="text-sm text-asphalt-mute">Loading…</div>;
  if (!issue) return <div className="text-sm text-asphalt-mute">Not found</div>;

  const errMsg = (err: unknown, fallback: string) => {
    const detail = (err as { response?: { data?: { error?: { detail?: unknown } } } })?.response?.data
      ?.error?.detail;
    return typeof detail === "string" ? detail : fallback;
  };

  const transition = async (status: string) => {
    try {
      await api.post(`/issues/${publicId}/transition/`, { status, comment });
      push("Updated", "success");
      setComment("");
      await load();
    } catch (err) {
      push(errMsg(err, "Transition failed"), "error");
    }
  };

  const assign = async (e: FormEvent) => {
    e.preventDefault();
    try {
      await api.post(`/issues/${publicId}/assign/`, { team_id: Number(teamId), notes: comment });
      push("Assigned", "success");
      await load();
    } catch (err) {
      push(errMsg(err, "Assign failed"), "error");
    }
  };

  const accept = async () => {
    try {
      await api.post(`/issues/${publicId}/accept/`);
      push("Accepted", "success");
      await load();
    } catch {
      push("Accept failed", "error");
    }
  };

  const resolve = async (e: FormEvent) => {
    e.preventDefault();
    const fd = new FormData();
    fd.append("notes", resolveNotes);
    try {
      await api.post(`/issues/${publicId}/resolve/`, fd);
      push("Resolved", "success");
      await load();
    } catch {
      push("Resolve failed", "error");
    }
  };

  const support = async () => {
    try {
      await api.post(`/issues/${publicId}/support/`, {});
      push("Supported", "success");
      await load();
    } catch {
      push("Support failed", "error");
    }
  };

  return (
    <div className="grid gap-8 lg:grid-cols-[1.6fr_0.9fr]">
      <div className="space-y-6">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge status={issue.status} />
            <PriorityBadge priority={issue.priority} />
          </div>
          <h1 className="page-title mt-3">{issue.title}</h1>
          <p className="mt-3 max-w-2xl text-[15px] leading-relaxed text-asphalt/85">{issue.description}</p>
        </div>

        <dl className="grid grid-cols-2 gap-x-4 gap-y-3 border-y border-asphalt/10 py-4 text-sm sm:grid-cols-3">
          {[
            ["Type", issue.category.replaceAll("_", " ").toLowerCase()],
            ["Severity", issue.severity.toLowerCase()],
            ["Supports", String(issue.support_count)],
            ["Team", issue.assigned_team?.name || "—"],
            ["Place", issue.address || `${issue.latitude}, ${issue.longitude}`],
            ["Score", String(issue.priority_score)],
          ].map(([k, v]) => (
            <div key={k}>
              <dt className="text-xs uppercase tracking-wide text-asphalt-mute">{k}</dt>
              <dd className="mt-0.5 font-medium">{v}</dd>
            </div>
          ))}
        </dl>

        {issue.images && issue.images.length > 0 && (
          <div className="grid gap-3 sm:grid-cols-2">
            {issue.images.map((img) => (
              <img key={img.id} src={img.image} alt="" className="h-44 w-full object-cover" />
            ))}
          </div>
        )}

        <div>
          <h2 className="font-display text-lg font-bold">Timeline</h2>
          <ol className="mt-4 space-y-0">
            {(issue.status_history || []).map((h, idx) => (
              <li key={h.id} className="relative flex gap-4 pb-5 last:pb-0">
                <div className="flex flex-col items-center">
                  <span className="mt-1 h-2.5 w-2.5 rounded-full bg-signal" />
                  {idx < (issue.status_history?.length || 0) - 1 && (
                    <span className="w-px flex-1 bg-asphalt/15" />
                  )}
                </div>
                <div className="pb-1">
                  <div className="text-sm font-semibold">
                    {(h.previous_status || "new").toLowerCase()} → {h.new_status.toLowerCase()}
                  </div>
                  <div className="text-xs text-asphalt-mute">
                    {h.actor?.username || "system"} · {new Date(h.created_at).toLocaleString()}
                  </div>
                  {h.comment && <div className="mt-1 text-sm text-asphalt/80">{h.comment}</div>}
                </div>
              </li>
            ))}
          </ol>
        </div>
      </div>

      <aside className="space-y-3 lg:sticky lg:top-20 lg:self-start">
        {user?.role === "CITIZEN" && issue.reporter?.id !== user.id && (
          <div className="shell p-4">
            <button className="btn-signal w-full" onClick={support}>
              Support this report
            </button>
          </div>
        )}

        {user?.role === "ADMIN" && (
          <div className="shell space-y-3 p-4">
            <textarea
              className="input min-h-16"
              placeholder="Note"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
            />
            <div className="grid grid-cols-2 gap-2">
              <button className="btn-secondary !text-xs" onClick={() => transition("UNDER_REVIEW")}>
                Review
              </button>
              <button className="btn-secondary !text-xs" onClick={() => transition("VERIFIED")}>
                Verify
              </button>
              <button className="btn-danger col-span-2 !text-xs" onClick={() => transition("REJECTED")}>
                Reject
              </button>
            </div>
            <form onSubmit={assign} className="space-y-2 border-t border-asphalt/10 pt-3">
              <select className="input" value={teamId} onChange={(e) => setTeamId(e.target.value)}>
                {teams.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                  </option>
                ))}
              </select>
              <button className="btn-primary w-full">Assign team</button>
            </form>
          </div>
        )}

        {user?.role === "MAINTENANCE" && (
          <div className="shell space-y-3 p-4">
            {issue.status === "ASSIGNED" && (
              <button className="btn-signal w-full" onClick={accept}>
                Accept job
              </button>
            )}
            {(issue.status === "IN_PROGRESS" || issue.status === "ASSIGNED") && (
              <form onSubmit={resolve} className="space-y-2">
                <textarea
                  className="input min-h-20"
                  placeholder="Resolution notes"
                  value={resolveNotes}
                  onChange={(e) => setResolveNotes(e.target.value)}
                />
                <button className="btn-primary w-full">Mark resolved</button>
              </form>
            )}
          </div>
        )}
      </aside>
    </div>
  );
}
