import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { useToast } from "../components/Toast";

export function RegisterPage() {
  const { register, login } = useAuth();
  const { push } = useToast();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    password_confirm: "",
    first_name: "",
    last_name: "",
  });
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await register(form);
      await login(form.username, form.password);
      push("Account ready", "success");
      navigate("/citizen");
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { error?: { detail?: unknown } } } })?.response?.data
        ?.error?.detail;
      const msg =
        typeof detail === "string"
          ? detail
          : detail
            ? JSON.stringify(detail)
            : "Registration failed — check API connection";
      push(msg.slice(0, 120), "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto flex min-h-screen max-w-md items-center px-4">
      <form onSubmit={onSubmit} className="shell w-full animate-rise p-8">
        <Link to="/login" className="font-display text-2xl font-extrabold text-asphalt">
          CityFix
        </Link>
        <h1 className="mt-6 page-title !text-2xl">Join as citizen</h1>
        <div className="mt-6 grid gap-3 sm:grid-cols-2">
          {(
            [
              ["first_name", "First"],
              ["last_name", "Last"],
              ["username", "Username"],
              ["email", "Email"],
              ["password", "Password"],
              ["password_confirm", "Confirm"],
            ] as const
          ).map(([key, label]) => (
            <div
              key={key}
              className={
                key === "username" || key === "email" || key.includes("password")
                  ? "sm:col-span-2"
                  : ""
              }
            >
              <label className="label">{label}</label>
              <input
                className="input"
                type={key.includes("password") ? "password" : key === "email" ? "email" : "text"}
                value={form[key]}
                onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                required
              />
            </div>
          ))}
        </div>
        <button className="btn-signal mt-6 w-full" disabled={loading}>
          {loading ? "…" : "Create account"}
        </button>
      </form>
    </div>
  );
}
