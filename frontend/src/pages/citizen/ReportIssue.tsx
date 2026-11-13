import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../../api/client";
import { useToast } from "../../components/Toast";
import type { DuplicateSuggestion } from "../../types";

const CATEGORIES = [
  ["POTHOLE", "Pothole"],
  ["STREETLIGHT", "Streetlight"],
  ["GARBAGE", "Garbage"],
  ["WATER_LEAK", "Water leak"],
  ["OTHER", "Other"],
];

export function ReportIssue() {
  const { push } = useToast();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    title: "",
    description: "",
    category: "POTHOLE",
    severity: "MODERATE",
    latitude: "12.971600",
    longitude: "77.594600",
    address: "",
  });
  const [image, setImage] = useState<File | null>(null);
  const [suggestions, setSuggestions] = useState<DuplicateSuggestion[]>([]);
  const [loading, setLoading] = useState(false);

  const buildPayload = (force = false) => {
    const fd = new FormData();
    Object.entries(form).forEach(([k, v]) => fd.append(k, v));
    if (force) fd.append("force", "true");
    if (image) fd.append("image", image);
    return fd;
  };

  const submit = async (force = false) => {
    setLoading(true);
    try {
      const { data, status } = await api.post("/issues/", buildPayload(force), {
        validateStatus: (s) => (s >= 200 && s < 300) || s === 409,
      });
      if (status === 409) {
        setSuggestions(data.duplicate_suggestions || []);
        push("Similar report nearby", "info");
        return;
      }
      push("Report filed", "success");
      navigate(`/issues/${data.issue.public_id}`);
    } catch {
      push("Submit failed", "error");
    } finally {
      setLoading(false);
    }
  };

  const supportExisting = async (publicId: string) => {
    try {
      await api.post(`/issues/${publicId}/support/`, { note: "Supported via duplicate suggestion" });
      push("Supported existing report", "success");
      navigate(`/issues/${publicId}`);
    } catch {
      push("Could not support", "error");
    }
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <h1 className="page-title">New report</h1>

      <form
        onSubmit={(e: FormEvent) => {
          e.preventDefault();
          void submit(false);
        }}
        className="shell space-y-4 p-5 sm:p-6"
      >
        <div>
          <label className="label">Title</label>
          <input
            className="input"
            required
            placeholder="e.g. Deep pothole on MG Road"
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
          />
        </div>
        <div>
          <label className="label">What happened</label>
          <textarea
            className="input min-h-24"
            required
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
          />
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="label">Type</label>
            <select
              className="input"
              value={form.category}
              onChange={(e) => setForm({ ...form, category: e.target.value })}
            >
              {CATEGORIES.map(([v, l]) => (
                <option key={v} value={v}>
                  {l}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Severity</label>
            <select
              className="input"
              value={form.severity}
              onChange={(e) => setForm({ ...form, severity: e.target.value })}
            >
              {["MINOR", "MODERATE", "MAJOR", "SEVERE"].map((s) => (
                <option key={s} value={s}>
                  {s.toLowerCase()}
                </option>
              ))}
            </select>
          </div>
        </div>
        <div>
          <label className="label">Address</label>
          <input
            className="input"
            placeholder="Street / landmark"
            value={form.address}
            onChange={(e) => setForm({ ...form, address: e.target.value })}
          />
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="label">Lat</label>
            <input
              className="input"
              required
              value={form.latitude}
              onChange={(e) => setForm({ ...form, latitude: e.target.value })}
            />
          </div>
          <div>
            <label className="label">Lng</label>
            <input
              className="input"
              required
              value={form.longitude}
              onChange={(e) => setForm({ ...form, longitude: e.target.value })}
            />
          </div>
        </div>
        <div>
          <label className="label">Photo</label>
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            className="block w-full text-sm text-asphalt-mute file:mr-3 file:border-0 file:bg-asphalt file:px-3 file:py-2 file:text-sm file:font-semibold file:text-white"
            onChange={(e) => setImage(e.target.files?.[0] || null)}
          />
        </div>
        <button className="btn-signal" disabled={loading}>
          {loading ? "Checking…" : "Submit"}
        </button>
      </form>

      {suggestions.length > 0 && (
        <div className="border border-signal bg-signal-soft p-5">
          <h2 className="font-display text-lg font-bold">Already reported nearby</h2>
          <div className="mt-4 space-y-3">
            {suggestions.map((s) => (
              <div key={s.public_id} className="flex flex-wrap items-center justify-between gap-3 bg-white p-3">
                <div>
                  <Link className="font-semibold text-asphalt" to={`/issues/${s.public_id}`}>
                    {s.title}
                  </Link>
                  <div className="text-xs text-asphalt-mute">
                    {Math.round(s.distance_meters)}m · {s.support_count} supports
                  </div>
                </div>
                <button className="btn-primary !py-2" onClick={() => supportExisting(s.public_id)}>
                  Support instead
                </button>
              </div>
            ))}
          </div>
          <button className="btn-secondary mt-4" disabled={loading} onClick={() => submit(true)}>
            File as new anyway
          </button>
        </div>
      )}
    </div>
  );
}
