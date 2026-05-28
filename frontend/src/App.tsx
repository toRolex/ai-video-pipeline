import { Routes, Route, Link, useLocation } from "react-router-dom";
import ProjectList from "./pages/ProjectList";
import ProjectWorkbench from "./pages/ProjectWorkbench";
import JobPipeline from "./pages/JobPipeline";
import ConfigPage from "./pages/ConfigPage";
import ErrorBoundary from "./components/ErrorBoundary";

function NavLink({ to, label }: { to: string; label: string }) {
  const location = useLocation();
  const active = location.pathname === to;
  return (
    <Link
      to={to}
      className={`px-3 py-2 rounded-xl text-sm font-medium transition-colors ${
        active
          ? "text-[#0969da] bg-[#eff2f5]"
          : "text-[#59636e] hover:text-gray-700 hover:bg-gray-50"
      }`}
    >
      {label}
    </Link>
  );
}

export default function App() {
  return (
    <div className="max-w-6xl mx-auto px-4 py-4">
      <nav className="flex items-center gap-2 pb-3 border-b border-gray-200 mb-6">
        <NavLink to="/" label="项目列表" />
        <NavLink to="/config" label="系统配置" />
      </nav>
      <ErrorBoundary>
        <Routes>
          <Route path="/" element={<ProjectList />} />
          <Route path="/projects/:id" element={<ProjectWorkbench />} />
          <Route path="/jobs/:id" element={<JobPipeline />} />
          <Route path="/config" element={<ConfigPage />} />
        </Routes>
      </ErrorBoundary>
    </div>
  );
}
