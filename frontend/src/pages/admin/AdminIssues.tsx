import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../api/client";
import { PriorityBadge, StatusBadge } from "../../components/StatusBadge";
import type { Issue } from "../../types";

export function AdminIssues() {
  const [issues, setIssues] = useState<Issue[]>([]);
  const [status, setStatus] = useState("");
  const [category, setCategory] = useState("");
  const [priority, setPriority] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .get("/issues/", {
        params: {
          ...(status ? { status } : {}),
          ...(category ? { category } : {}),
          ...(priority ? { priority } : {}),
          ordering: "-priority_score",
        },
      })
      .then((res) => setIssues(res.data.results ?? res.data))
      .finally(() => setLoading(false));
  }, [status, category, priority]);

  return (
    <div className="space-y-5">
      <h1 className="page-title">Issues</h1>
      <div className="flex flex-wrap gap-2">
        {[
          [status, setStatus, "Status", ["REPORTED", "UNDER_REVIEW", "VERIFIED", "ASSIGNED", "IN_PROGRESS", "RESOLVED", "REJECTED"]],
          [category, setCategory, "Type", ["POTHOLE", "STREETLIGHT", "GARBAGE", "WATER_LEAK", "OTHER"]],
          [priority, setPriority, "Priority", ["LOW", "MEDIUM", "HIGH", "CRITICAL"]],
        ].map(([value, setter, label, opts]) => (
          <select
            key={String(label)}
            className="input max-w-[150px]"
            value={value as string}
            onChange={(e) => (setter as (v: string) => void)(e.target.value)}
          >
            <option value="">{label as string}</option>
            {(opts as string[]).map((s) => (
              <option key={s} value={s}>
                {s.replaceAll("_", " ").toLowerCase()}
              </option>
            ))}
          </select>
        ))}
      </div>

      <div className="shell overflow-x-auto">
        {loading ? (
          <div className="p-6 text-sm text-asphalt-mute">Loading…</div>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="border-b border-asphalt/10 text-xs uppercase tracking-wide text-asphalt-mute">
              <tr>
                <th className="px-4 py-3 font-semibold">Issue</th>
                <th className="px-4 py-3 font-semibold">Reporter</th>
                <th className="px-4 py-3 font-semibold">Status</th>
                <th className="px-4 py-3 font-semibold">Priority</th>
                <th className="px-4 py-3 font-semibold">+</th>
              </tr>
            </thead>
            <tbody>
              {issues.map((issue) => (
                <tr key={issue.public_id} className="border-b border-asphalt/5 last:border-0 hover:bg-chalk-warm/60">
                  <td className="px-4 py-3">
                    <Link className="font-semibold text-asphalt hover:underline" to={`/issues/${issue.public_id}`}>
                      {issue.title}
                    </Link>
                    <div className="text-xs text-asphalt-mute">
                      {issue.category.replaceAll("_", " ").toLowerCase()}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-asphalt-mute">{issue.reporter_name}</td>
                  <td className="px-4 py-3">
                    <StatusBadge status={issue.status} />
                  </td>
                  <td className="px-4 py-3">
                    <PriorityBadge priority={issue.priority} />
                  </td>
                  <td className="px-4 py-3 text-asphalt-mute">{issue.support_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
