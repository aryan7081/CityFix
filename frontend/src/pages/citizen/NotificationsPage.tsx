import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../api/client";
import { useToast } from "../../components/Toast";
import type { NotificationItem } from "../../types";

export function NotificationsPage() {
  const { push } = useToast();
  const [items, setItems] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    api
      .get("/notifications/")
      .then((res) => setItems(res.data.results ?? res.data))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const markAll = async () => {
    await api.post("/notifications/mark-all-read/");
    push("Inbox cleared", "success");
    load();
  };

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-3">
        <h1 className="page-title">Inbox</h1>
        <button className="btn-secondary !py-2 !text-xs" onClick={markAll}>
          Mark all read
        </button>
      </div>
      <div className="shell divide-y divide-asphalt/10">
        {loading ? (
          <div className="p-6 text-sm text-asphalt-mute">Loading…</div>
        ) : items.length === 0 ? (
          <div className="px-6 py-14 text-center text-asphalt-mute">Quiet for now</div>
        ) : (
          items.map((n) => (
            <div key={n.id} className={`px-4 py-4 ${n.is_read ? "opacity-55" : ""}`}>
              <div className="font-semibold">{n.title}</div>
              <div className="mt-0.5 text-sm text-asphalt-mute">{n.message}</div>
              <div className="mt-2 flex gap-3 text-xs text-asphalt-mute">
                <span>{new Date(n.created_at).toLocaleString()}</span>
                {n.issue_public_id && (
                  <Link className="font-semibold text-asphalt underline decoration-signal" to={`/issues/${n.issue_public_id}`}>
                    Open
                  </Link>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
