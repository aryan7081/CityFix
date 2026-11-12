import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { useToast } from "../components/Toast";

export function LoginPage() {
  const { login } = useAuth();
  const { push } = useToast();
  const navigate = useNavigate();
  const [username, setUsername] = useState("citizen1");
  const [password, setPassword] = useState("citizen123");
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const user = await login(username, password);
      push(`Welcome, ${user.username}`, "success");
      navigate("/");
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status;
      push(status === 401 ? "Invalid credentials" : "Login failed — check API connection", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <section className="relative hidden overflow-hidden lg:block">
        <img
          src="https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?auto=format&fit=crop&w=1600&q=80"
          alt="City street at dusk"
          className="absolute inset-0 h-full w-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-asphalt via-asphalt/55 to-asphalt/20" />
        <div className="absolute inset-x-0 bottom-0 animate-rise p-10 text-white">
          <p className="font-display text-5xl font-extrabold tracking-tight">CityFix</p>
          <p className="mt-3 max-w-sm text-lg text-white/85">
            Report what&apos;s broken. Watch it get fixed.
          </p>
        </div>
      </section>

      <section className="flex items-center justify-center bg-chalk px-6 py-12">
        <form onSubmit={onSubmit} className="w-full max-w-sm animate-rise">
          <p className="font-display text-3xl font-extrabold lg:hidden">CityFix</p>
          <h1 className="mt-2 font-display text-2xl font-bold text-asphalt">Sign in</h1>

          <div className="mt-8 space-y-4">
            <div>
              <label className="label">Username</label>
              <input
                className="input"
                autoComplete="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
            </div>
            <div>
              <label className="label">Password</label>
              <input
                className="input"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            <button className="btn-signal w-full" disabled={loading}>
              {loading ? "…" : "Continue"}
            </button>
          </div>

          <p className="mt-5 text-sm text-asphalt-mute">
            New here?{" "}
            <Link className="font-semibold text-asphalt underline decoration-signal underline-offset-4" to="/register">
              Create account
            </Link>
          </p>

          <div className="mt-10 flex flex-wrap gap-2 text-[11px] text-asphalt-mute">
            {[
              ["citizen1", "citizen123"],
              ["admin", "admin123"],
              ["staff1", "staff123"],
            ].map(([u, p]) => (
              <button
                key={u}
                type="button"
                className="border border-asphalt/10 bg-white px-2 py-1 hover:border-asphalt/30"
                onClick={() => {
                  setUsername(u);
                  setPassword(p);
                }}
              >
                {u}
              </button>
            ))}
          </div>
        </form>
      </section>
    </div>
  );
}
