import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "../../api/client";
import { useToast } from "../../components/Toast";
import type { DashboardStats } from "../../types";

export function AdminDashboard() {
  const { push } = useToast();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  const load = async (bypass = false) => {
    setLoading(true);
    try {
      const { data } = await api.get("/analytics/dashboard/", {
        params: bypass ? { bypass_cache: 1 } : {},
      });
      setStats(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  if (loading && !stats) return <div className="text-sm text-asphalt-mute">Loading…</div>;
  if (!stats) return null;

  const metrics = [
    [stats.total_issues, "Total"],
    [stats.pending_verification, "Pending"],
    [stats.high_priority_open, "High priority"],
    [`${stats.resolution_rate_percent}%`, "Resolved"],
  ] as const;

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <h1 className="page-title">Overview</h1>
        <button
          className="btn-secondary !text-xs"
          onClick={async () => {
            await load(true);
            await load(false);
            push("Cache refreshed", "success");
          }}
        >
          Refresh cache
        </button>
      </div>

      <div className="grid grid-cols-2 gap-px bg-asphalt/10 sm:grid-cols-4">
        {metrics.map(([value, label]) => (
          <div key={label} className="bg-chalk px-4 py-5">
            <div className="font-display text-3xl font-extrabold tracking-tight">{value}</div>
            <div className="mt-1 text-xs uppercase tracking-wide text-asphalt-mute">{label}</div>
          </div>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="shell p-4">
          <h2 className="text-sm font-semibold text-asphalt-mute">Reports / day</h2>
          <div className="mt-3 h-56">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={stats.reported_over_time}>
                <CartesianGrid stroke="#e5e7eb" strokeDasharray="3 3" />
                <XAxis dataKey="day" hide />
                <YAxis allowDecimals={false} width={28} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Line type="monotone" dataKey="count" stroke="#e09a16" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="shell p-4">
          <h2 className="text-sm font-semibold text-asphalt-mute">By category</h2>
          <div className="mt-3 h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stats.by_category}>
                <CartesianGrid stroke="#e5e7eb" strokeDasharray="3 3" />
                <XAxis dataKey="category" tick={{ fontSize: 10 }} />
                <YAxis allowDecimals={false} width={28} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="count" fill="#2f4a63" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <p className="text-xs text-asphalt-mute">
        Avg resolution {stats.average_resolution_hours ?? "—"}h · duplicates{" "}
        {stats.duplicate_candidates_detected}
        {stats.cache_counters
          ? ` · cache ${String(stats.cache_counters.hits)}/${String(stats.cache_counters.misses)}`
          : ""}
      </p>
    </div>
  );
}
