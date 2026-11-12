import { Link, NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function Layout() {
  const { user, logout } = useAuth();

  const links =
    user?.role === "ADMIN"
      ? [
          { to: "/admin", label: "Overview" },
          { to: "/admin/issues", label: "Issues" },
          { to: "/admin/health", label: "Health" },
        ]
      : user?.role === "MAINTENANCE"
        ? [{ to: "/staff", label: "Work queue" }]
        : [
            { to: "/citizen", label: "Reports" },
            { to: "/citizen/report", label: "New" },
            { to: "/citizen/notifications", label: "Inbox" },
          ];

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-40 border-b border-asphalt/10 bg-chalk/90 backdrop-blur-md">
        <div className="mx-auto flex h-14 max-w-6xl items-center gap-6 px-4">
          <Link to="/" className="font-display text-xl font-extrabold tracking-tight text-asphalt">
            CityFix
          </Link>
          <nav className="flex flex-1 items-center gap-1 overflow-x-auto">
            {links.map((l) => (
              <NavLink
                key={l.to}
                to={l.to}
                end={l.to === "/admin" || l.to === "/citizen" || l.to === "/staff"}
                className={({ isActive }) =>
                  `relative px-3 py-2 text-sm font-semibold transition ${
                    isActive ? "text-asphalt" : "text-asphalt-mute hover:text-asphalt"
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    {l.label}
                    <span
                      className={`absolute inset-x-3 -bottom-[13px] h-0.5 bg-signal transition ${
                        isActive ? "opacity-100" : "opacity-0"
                      }`}
                    />
                  </>
                )}
              </NavLink>
            ))}
          </nav>
          <div className="flex items-center gap-3">
            <span className="hidden text-sm font-medium text-asphalt-mute sm:inline">
              {user?.username}
            </span>
            <button className="btn-secondary !py-1.5 !text-xs" onClick={logout}>
              Out
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl animate-rise px-4 py-8">
        <Outlet />
      </main>
    </div>
  );
}
