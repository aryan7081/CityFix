import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth/AuthContext";
import { Layout } from "./components/Layout";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { CitizenHome } from "./pages/citizen/CitizenHome";
import { ReportIssue } from "./pages/citizen/ReportIssue";
import { IssueDetail } from "./pages/IssueDetail";
import { NotificationsPage } from "./pages/citizen/NotificationsPage";
import { AdminDashboard } from "./pages/admin/AdminDashboard";
import { AdminIssues } from "./pages/admin/AdminIssues";
import { SystemHealth } from "./pages/admin/SystemHealth";
import { StaffHome } from "./pages/staff/StaffHome";
import type { Role } from "./types";

function Protected({ roles, children }: { roles?: Role[]; children: React.ReactNode }) {
  const { user, isAuthenticated } = useAuth();
  if (!isAuthenticated || !user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.role)) {
    const home =
      user.role === "ADMIN" ? "/admin" : user.role === "MAINTENANCE" ? "/staff" : "/citizen";
    return <Navigate to={home} replace />;
  }
  return <>{children}</>;
}

function HomeRedirect() {
  const { user, isAuthenticated } = useAuth();
  if (!isAuthenticated || !user) return <Navigate to="/login" replace />;
  if (user.role === "ADMIN") return <Navigate to="/admin" replace />;
  if (user.role === "MAINTENANCE") return <Navigate to="/staff" replace />;
  return <Navigate to="/citizen" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/" element={<HomeRedirect />} />
      <Route
        element={
          <Protected>
            <Layout />
          </Protected>
        }
      >
        <Route
          path="/citizen"
          element={
            <Protected roles={["CITIZEN"]}>
              <CitizenHome />
            </Protected>
          }
        />
        <Route
          path="/citizen/report"
          element={
            <Protected roles={["CITIZEN"]}>
              <ReportIssue />
            </Protected>
          }
        />
        <Route
          path="/citizen/notifications"
          element={
            <Protected roles={["CITIZEN", "ADMIN", "MAINTENANCE"]}>
              <NotificationsPage />
            </Protected>
          }
        />
        <Route path="/issues/:publicId" element={<IssueDetail />} />
        <Route
          path="/admin"
          element={
            <Protected roles={["ADMIN"]}>
              <AdminDashboard />
            </Protected>
          }
        />
        <Route
          path="/admin/issues"
          element={
            <Protected roles={["ADMIN"]}>
              <AdminIssues />
            </Protected>
          }
        />
        <Route
          path="/admin/health"
          element={
            <Protected roles={["ADMIN"]}>
              <SystemHealth />
            </Protected>
          }
        />
        <Route
          path="/staff"
          element={
            <Protected roles={["MAINTENANCE"]}>
              <StaffHome />
            </Protected>
          }
        />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
