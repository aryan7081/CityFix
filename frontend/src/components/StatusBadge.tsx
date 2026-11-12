const STATUS: Record<string, string> = {
  REPORTED: "bg-steel-soft text-steel",
  UNDER_REVIEW: "bg-signal-soft text-signal-deep",
  VERIFIED: "bg-emerald-50 text-ok",
  ASSIGNED: "bg-slate-100 text-asphalt",
  IN_PROGRESS: "bg-orange-50 text-orange-800",
  RESOLVED: "bg-emerald-100 text-ok",
  REJECTED: "bg-red-50 text-bad",
};

const PRIORITY: Record<string, string> = {
  LOW: "bg-slate-100 text-asphalt-mute",
  MEDIUM: "bg-steel-soft text-steel",
  HIGH: "bg-signal-soft text-signal-deep",
  CRITICAL: "bg-red-50 text-bad",
};

const label = (v: string) => v.replaceAll("_", " ").toLowerCase();

export function StatusBadge({ status }: { status: string }) {
  return <span className={`status-chip ${STATUS[status] || "bg-slate-100"}`}>{label(status)}</span>;
}

export function PriorityBadge({ priority }: { priority: string }) {
  return <span className={`status-chip ${PRIORITY[priority] || "bg-slate-100"}`}>{label(priority)}</span>;
}
