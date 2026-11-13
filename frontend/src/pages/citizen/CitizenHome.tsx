import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../api/client";
import { PriorityBadge, StatusBadge } from "../../components/StatusBadge";
import type { Issue } from "../../types";

export function CitizenHome() {
  const [issues, setIssues] = useState<Issue[]>([]);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState("");

  useEffect(() => {
    setLoading(true);
    api
      .get("/issues/", { params: status ? { status } : {} })
      .then((res) => setIssues(res.data.results ?? res.data))
      .finally(() => setLoading(false));
  }, [status]);

  const open = issues.filter((i) => !["RESOLVED", "REJECTED"].includes(i.status)).length;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="page-title">Your reports</h1>
          <p className="mt-1 text-sm text-asphalt-mute">
            {open} open · {issues.length} total
          </p>
        </div>
        <Link to="/citizen/report" className="btn-signal">
          Report issue
        </Link>
      </div>

      <div className="flex items-center gap-3">
        <select className="input max-w-[200px]" value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All</option>
          {["REPORTED", "UNDER_REVIEW", "VERIFIED", "ASSIGNED", "IN_PROGRESS", "RESOLVED", "REJECTED"].map(
            (s) => (
              <option key={s} value={s}>
                {s.replaceAll("_", " ")}
              </option>
            )
          )}
        </select>
      </div>

      <div className="shell overflow-hidden">
        {loading ? (
          <div className="p-8 text-sm text-asphalt-mute">Loading…</div>
        ) : issues.length === 0 ? (
          <div className="px-6 py-16 text-center">
            <p className="font-display text-xl font-bold">Nothing reported yet</p>
            <Link to="/citizen/report" className="btn-primary mt-5 inline-flex">
              File first report
            </Link>
          </div>
        ) : (
          <ul className="divide-y divide-asphalt/10">
            {issues.map((issue) => (
              <li key={issue.public_id}>
                <Link
                  to={`/issues/${issue.public_id}`}
                  className="flex flex-wrap items-center justify-between gap-3 px-4 py-4 transition hover:bg-chalk-warm/70"
                >
                  <div className="min-w-0">
                    <div className="truncate font-semibold text-asphalt">{issue.title}</div>
                    <div className="mt-0.5 text-xs text-asphalt-mute">
                      {issue.category.replaceAll("_", " ").toLowerCase()}
                      {issue.address ? ` · ${issue.address}` : ""}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <PriorityBadge priority={issue.priority} />
                    <StatusBadge status={issue.status} />
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
