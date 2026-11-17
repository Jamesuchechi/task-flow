import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Activity,
  ArrowRight,
  CheckSquare,
  FileUp,
  Layers,
  Paperclip,
  Radio,
  Search,
  Sparkles,
} from "lucide-react";
import { fetchHealth } from "../api/auth";
import { useAuth } from "../context/AuthContext";

const FEATURES = [
  {
    icon: Search,
    title: "Fast Search & Pagination",
    description:
      "Filter by status, search across titles and descriptions, sort by due date, and browse paginated results backed by TTL caching.",
    accent: "bg-indigo-50 text-indigo-600",
  },
  {
    icon: Paperclip,
    title: "Task File Attachments",
    description:
      "Upload specs, screenshots, or documents directly to any task with extension checks, size limits, and secure downloads.",
    accent: "bg-sky-50 text-sky-600",
  },
  {
    icon: Layers,
    title: "Background Jobs & Exports",
    description:
      "Queue asynchronous JSON or CSV task exports and generate overdue task digests without blocking your workflow.",
    accent: "bg-amber-50 text-amber-600",
  },
  {
    icon: Radio,
    title: "Real-Time WebSockets",
    description:
      "Stay in sync with live WebSocket notifications whenever tasks, attachments, or background jobs update.",
    accent: "bg-emerald-50 text-emerald-600",
  },
];

export function LandingPage() {
  const { isAuthenticated, user } = useAuth();
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);

  useEffect(() => {
    let active = true;
    fetchHealth()
      .then((res) => {
        if (active) setApiOnline(res.status === "ok");
      })
      .catch(() => {
        if (active) setApiOnline(false);
      });
    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      {/* Top Navbar */}
      <header className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/85 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3.5 sm:px-6">
          <Link to="/" className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-600 text-white shadow-sm">
              <CheckSquare className="h-5 w-5" />
            </div>
            <span className="text-lg font-bold tracking-tight text-slate-900">
              TaskFlow
            </span>
          </Link>

          <div className="flex items-center gap-3">
            {/* Live API Status Pill */}
            <div
              title="Backend API Health"
              className="hidden items-center gap-1.5 rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-600 sm:flex"
            >
              <span
                className={`h-2 w-2 rounded-full ${
                  apiOnline === true
                    ? "bg-emerald-500"
                    : apiOnline === false
                      ? "bg-rose-500"
                      : "animate-pulse bg-slate-400"
                }`}
              />
              {apiOnline === true
                ? "API Online"
                : apiOnline === false
                  ? "API Offline"
                  : "Checking API..."}
            </div>

            {isAuthenticated ? (
              <Link
                to="/dashboard"
                className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-indigo-700"
              >
                Go to Dashboard
                <ArrowRight className="h-4 w-4" />
              </Link>
            ) : (
              <>
                <Link
                  to="/login"
                  className="rounded-lg px-3.5 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-100"
                >
                  Sign In
                </Link>
                <Link
                  to="/register"
                  className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-indigo-700"
                >
                  Get Started
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main>
        <section className="mx-auto max-w-6xl px-4 pt-14 pb-16 sm:px-6 lg:pt-20">
          <div className="grid items-center gap-12 lg:grid-cols-12">
            <div className="lg:col-span-7">
              <div className="inline-flex items-center gap-2 rounded-full border border-indigo-200 bg-indigo-50 px-3.5 py-1 text-xs font-semibold text-indigo-700">
                <Sparkles className="h-3.5 w-3.5" />
                Real-Time Task Workspace
              </div>

              <h1 className="mt-5 text-4xl font-extrabold tracking-tight text-slate-900 sm:text-5xl">
                Organize tasks, files, and exports in{" "}
                <span className="text-indigo-600">real time</span>.
              </h1>

              <p className="mt-4 max-w-xl text-base leading-relaxed text-slate-600 sm:text-lg">
                TaskFlow pairs a fast FastAPI backend with live WebSocket sync,
                paginated search, file attachments, and asynchronous background
                jobs — built for clean, distraction-free productivity.
              </p>

              <div className="mt-8 flex flex-wrap items-center gap-3.5">
                {isAuthenticated ? (
                  <Link
                    to="/dashboard"
                    className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-700"
                  >
                    Open Dashboard {user ? `(${user.username})` : ""}
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                ) : (
                  <>
                    <Link
                      to="/register"
                      className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-700"
                    >
                      Get Started Free
                      <ArrowRight className="h-4 w-4" />
                    </Link>
                    <Link
                      to="/login"
                      className="inline-flex items-center gap-2 rounded-xl border border-slate-300 bg-white px-5 py-3 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50"
                    >
                      Sign In
                    </Link>
                  </>
                )}
              </div>
            </div>

            {/* Mini Workspace Preview Card */}
            <div className="lg:col-span-5">
              <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-lg">
                <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                  <div className="flex items-center gap-2">
                    <Activity className="h-4 w-4 text-indigo-600" />
                    <span className="text-xs font-semibold text-slate-700">
                      Workspace Preview
                    </span>
                  </div>
                  <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-[11px] font-medium text-emerald-700">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                    Live Sync
                  </span>
                </div>

                <div className="mt-4 space-y-2.5">
                  <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50/70 p-3">
                    <div>
                      <p className="text-sm font-medium text-slate-800">
                        Finalize API documentation
                      </p>
                      <p className="mt-0.5 flex items-center gap-1.5 text-xs text-slate-500">
                        <FileUp className="h-3.5 w-3.5" />
                        2 attachments
                      </p>
                    </div>
                    <span className="rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-medium text-emerald-700">
                      Done
                    </span>
                  </div>

                  <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-3">
                    <div>
                      <p className="text-sm font-medium text-slate-800">
                        Export sprint tasks to CSV
                      </p>
                      <p className="mt-0.5 text-xs text-slate-500">
                        Background job completed
                      </p>
                    </div>
                    <span className="rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-medium text-blue-700">
                      In Progress
                    </span>
                  </div>

                  <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-3">
                    <div>
                      <p className="text-sm font-medium text-slate-800">
                        Review overdue digest
                      </p>
                      <p className="mt-0.5 text-xs text-slate-500">
                        Due tomorrow
                      </p>
                    </div>
                    <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-700">
                      Todo
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* 4-Card Feature Grid */}
        <section className="border-t border-slate-200 bg-white py-16">
          <div className="mx-auto max-w-6xl px-4 sm:px-6">
            <div className="max-w-2xl">
              <h2 className="text-2xl font-bold tracking-tight text-slate-900">
                Everything wired end-to-end
              </h2>
              <p className="mt-2 text-sm text-slate-600">
                Built around real-world backend patterns so every feature works
                seamlessly from UI to database.
              </p>
            </div>

            <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
              {FEATURES.map((feature) => {
                const Icon = feature.icon;
                return (
                  <div
                    key={feature.title}
                    className="rounded-2xl border border-slate-200 bg-slate-50/50 p-5 transition hover:border-slate-300 hover:bg-white hover:shadow-sm"
                  >
                    <div
                      className={`inline-flex h-10 w-10 items-center justify-center rounded-xl ${feature.accent}`}
                    >
                      <Icon className="h-5 w-5" />
                    </div>
                    <h3 className="mt-4 text-base font-semibold text-slate-900">
                      {feature.title}
                    </h3>
                    <p className="mt-1.5 text-sm leading-relaxed text-slate-600">
                      {feature.description}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-slate-200 bg-slate-50 py-6 text-center text-xs text-slate-500">
        TaskFlow • FastAPI + React + TypeScript
      </footer>
    </div>
  );
}
