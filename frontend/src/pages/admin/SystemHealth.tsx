import { useEffect, useState } from "react";
import { api } from "../../api/client";

export function SystemHealth() {
  const [data, setData] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    api
      .get("/analytics/system-health/")
      .then((res) => setData(res.data))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  if (loading && !data) return <div className="text-sm text-asphalt-mute">Probing…</div>;
  if (!data) return null;

  const components = data.components as Record<string, Record<string, unknown>>;
  const cache = data.cache as Record<string, unknown>;
  const apiMetrics = data.api as Record<string, unknown>;

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between">
        <h1 className="page-title">Health</h1>
        <button className="btn-secondary !text-xs" onClick={load}>
          Refresh
        </button>
      </div>

      <div className="grid gap-px bg-asphalt/10 sm:grid-cols-3">
        {Object.entries(components).map(([name, info]) => (
          <div key={name} className="bg-chalk p-5">
            <div className="text-xs uppercase tracking-wide text-asphalt-mute">{name}</div>
            <div className={`mt-2 font-display text-2xl font-extrabold ${info.status === "up" ? "text-ok" : "text-bad"}`}>
              {String(info.status)}
            </div>
            {info.latency_ms != null && (
              <div className="mt-1 text-xs text-asphalt-mute">{String(info.latency_ms)} ms</div>
            )}
          </div>
        ))}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="shell p-5 text-sm">
          <h2 className="font-display text-lg font-bold">Cache</h2>
          <ul className="mt-3 space-y-1 text-asphalt/80">
            <li>Hits {String(cache.hits)}</li>
            <li>Misses {String(cache.misses)}</li>
            <li>Invalidations {String(cache.invalidations)}</li>
            <li>Celery tasks {String(cache.celery_tasks_processed)}</li>
          </ul>
        </div>
        <div className="shell p-5 text-sm">
          <h2 className="font-display text-lg font-bold">API</h2>
          <p className="mt-3">
            Avg {String(apiMetrics.average_response_ms ?? "—")} ms
          </p>
          <p className="mt-2 text-xs text-asphalt-mute">
            Duplicates {(data.duplicates as { detected_total: number }).detected_total}
          </p>
        </div>
      </div>
    </div>
  );
}
