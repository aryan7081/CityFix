import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../api/client";
import { PriorityBadge, StatusBadge } from "../../components/StatusBadge";
import type { Issue } from "../../types";

export function StaffHome() {
  const [issues, setIssues] = useState<Issue[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get("/issues/", { params: { ordering: "-priority_score" } })
      .then((res) => setIssues(res.data.results ?? res.data))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-5">
      <h1 className="page-title">Work queue</h1>
      <div className="shell divide-y divide-asphalt/10">
        {loading ? (
          <div className="p-6 text-sm text-asphalt-mute">Loading…</div>
        ) : issues.length === 0 ? (
          <div className="px-6 py-14 text-center text-asphalt-mute">No jobs assigned</div>
        ) : (
          issues.map((issue) => (
            <Link
              key={issue.public_id}
              to={`/issues/${issue.public_id}`}
              className="flex flex-wrap items-center justify-between gap-3 px-4 py-4 hover:bg-chalk-warm/70"
            >
              <div>
                <div className="font-semibold">{issue.title}</div>
                <div className="text-xs text-asphalt-mute">
                  {issue.address || issue.category.replaceAll("_", " ").toLowerCase()}
                </div>
              </div>
              <div className="flex gap-2">
                <PriorityBadge priority={issue.priority} />
                <StatusBadge status={issue.status} />
              </div>
            </Link>
          ))
        )}
      </div>
    </div>
  );
}
