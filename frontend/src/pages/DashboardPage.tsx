import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  ArrowUpDown,
  Calendar,
  CheckSquare,
  Database,
  Layers,
  Loader2,
  LogOut,
  Paperclip,
  Plus,
  Search,
} from "lucide-react";
import { ApiError } from "../api/client";
import {
  fetchTask,
  fetchTasks,
  updateTask,
  type SortOrder,
  type TaskSortBy,
} from "../api/tasks";
import { JobsPanel } from "../components/JobsPanel";
import { Pagination } from "../components/Pagination";
import { TaskDetailDrawer } from "../components/TaskDetailDrawer";
import { TaskModal } from "../components/TaskModal";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { useDebounce } from "../hooks/useDebounce";
import { useWebSocket } from "../hooks/useWebSocket";
import type {
  PaginatedResponse,
  TaskRead,
  TaskStatus,
  WsEventMessage,
} from "../types/api";

const STATUS_BADGE: Record<TaskStatus, string> = {
  todo: "bg-slate-100 text-slate-700",
  in_progress: "bg-blue-50 text-blue-700",
  done: "bg-emerald-50 text-emerald-700",
};

const STATUS_LABEL: Record<TaskStatus, string> = {
  todo: "Todo",
  in_progress: "In Progress",
  done: "Done",
};

export function DashboardPage() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { addToast } = useToast();

  const [activeTab, setActiveTab] = useState<"tasks" | "jobs">("tasks");

  // Task list query state
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [statusFilter, setStatusFilter] = useState<TaskStatus | "">("");
  const [searchInput, setSearchInput] = useState("");
  const debouncedSearch = useDebounce(searchInput, 300);
  const [sortBy, setSortBy] = useState<TaskSortBy>("created_at");
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc");

  const [tasksPage, setTasksPage] =
    useState<PaginatedResponse<TaskRead> | null>(null);
  const [cacheStatus, setCacheStatus] = useState<string | null>(null);
  const [isLoadingTasks, setIsLoadingTasks] = useState(true);

  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [selectedTask, setSelectedTask] = useState<TaskRead | null>(null);
  const [jobsRefreshSignal, setJobsRefreshSignal] = useState(0);

  const loadTasks = useCallback(async () => {
    setIsLoadingTasks(true);
    try {
      const { data, cacheStatus: xCache } = await fetchTasks({
        page,
        pageSize,
        status: statusFilter,
        q: debouncedSearch,
        sortBy,
        sortOrder,
      });
      setTasksPage(data);
      setCacheStatus(xCache);
    } catch (err) {
      addToast(
        err instanceof ApiError ? err.message : "Failed to load tasks",
        { variant: "error" }
      );
    } finally {
      setIsLoadingTasks(false);
    }
  }, [
    page,
    pageSize,
    statusFilter,
    debouncedSearch,
    sortBy,
    sortOrder,
    addToast,
  ]);

  useEffect(() => {
    void loadTasks();
  }, [loadTasks]);

  // Reset to page 1 when filters/search change
  useEffect(() => {
    setPage(1);
  }, [statusFilter, debouncedSearch, sortBy, sortOrder, pageSize]);

  const handleWsEvent = useCallback(
    (msg: WsEventMessage) => {
      if (
        msg.event === "task.created" ||
        msg.event === "task.updated" ||
        msg.event === "task.deleted" ||
        msg.event === "attachment.uploaded" ||
        msg.event === "attachment.deleted"
      ) {
        void loadTasks();
        if (
          selectedTask &&
          msg.data?.task_id === selectedTask.id &&
          msg.event !== "task.deleted"
        ) {
          fetchTask(selectedTask.id)
            .then(({ data }) => setSelectedTask(data))
            .catch(() => {});
        }
        if (msg.event === "task.deleted" && selectedTask?.id === msg.data?.task_id) {
          setSelectedTask(null);
        }
        addToast(`Sync: ${msg.event}`, { variant: "info", durationMs: 2500 });
      } else if (msg.event === "job.completed") {
        setJobsRefreshSignal((n) => n + 1);
        addToast("Background job completed", {
          message: String(msg.data?.job_type ?? ""),
          variant: "success",
        });
      } else if (msg.event === "job.failed") {
        setJobsRefreshSignal((n) => n + 1);
        addToast("Background job failed", {
          message: String(msg.data?.error ?? ""),
          variant: "error",
        });
      }
    },
    [loadTasks, selectedTask, addToast]
  );

  const wsStatus = useWebSocket(Boolean(user), handleWsEvent);

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  async function handleQuickStatusChange(task: TaskRead, nextStatus: TaskStatus) {
    try {
      const updated = await updateTask(task.id, { status: nextStatus });
      setTasksPage((prev) =>
        prev
          ? {
              ...prev,
              items: prev.items.map((t) => (t.id === updated.id ? updated : t)),
            }
          : prev
      );
      if (selectedTask?.id === updated.id) {
        setSelectedTask(updated);
      }
    } catch (err) {
      addToast(
        err instanceof ApiError ? err.message : "Failed to update status",
        { variant: "error" }
      );
    }
  }

  function isOverdue(task: TaskRead): boolean {
    if (!task.due_at || task.status === "done") return false;
    return new Date(task.due_at).getTime() < Date.now();
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      {/* Top Navbar */}
      <header className="sticky top-0 z-30 border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6">
          <div className="flex items-center gap-6">
            <Link to="/" className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-white">
                <CheckSquare className="h-4 w-4" />
              </div>
              <span className="text-base font-bold tracking-tight">
                TaskFlow
              </span>
            </Link>

            <nav className="flex items-center gap-1 rounded-xl bg-slate-100 p-1">
              <button
                type="button"
                onClick={() => setActiveTab("tasks")}
                className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition ${
                  activeTab === "tasks"
                    ? "bg-white text-slate-900 shadow-xs"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                Tasks
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("jobs")}
                className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition ${
                  activeTab === "jobs"
                    ? "bg-white text-slate-900 shadow-xs"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                <Layers className="h-3.5 w-3.5" />
                Background Jobs
              </button>
            </nav>
          </div>

          <div className="flex items-center gap-2.5">
            {/* WebSocket Status Pill */}
            <div
              title="WebSocket real-time connection"
              className="hidden items-center gap-1.5 rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs font-medium text-slate-600 sm:flex"
            >
              <span
                className={`h-2 w-2 rounded-full ${
                  wsStatus === "connected"
                    ? "bg-emerald-500"
                    : wsStatus === "reconnecting"
                      ? "animate-pulse bg-amber-500"
                      : "bg-slate-400"
                }`}
              />
              {wsStatus === "connected"
                ? "Live"
                : wsStatus === "reconnecting"
                  ? "Reconnecting"
                  : "Offline"}
            </div>

            {/* X-Cache Indicator */}
            {activeTab === "tasks" && cacheStatus && (
              <div
                title="Backend response cache status"
                className={`hidden items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium md:flex ${
                  cacheStatus === "HIT"
                    ? "bg-emerald-50 text-emerald-700"
                    : "bg-slate-100 text-slate-600"
                }`}
              >
                <Database className="h-3 w-3" />
                Cache: {cacheStatus}
              </div>
            )}

            <button
              type="button"
              onClick={() => setIsCreateOpen(true)}
              className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 px-3.5 py-2 text-xs font-semibold text-white shadow-xs hover:bg-indigo-700"
            >
              <Plus className="h-4 w-4" />
              New Task
            </button>

            <div className="flex items-center gap-2 border-l border-slate-200 pl-2.5">
              <span className="hidden text-xs font-medium text-slate-700 sm:inline">
                {user?.username}
              </span>
              <button
                type="button"
                onClick={handleLogout}
                title="Sign out"
                className="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-2.5 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-100 hover:text-slate-900"
              >
                <LogOut className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">Logout</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-6 sm:px-6">
        {activeTab === "jobs" ? (
          <JobsPanel refreshSignal={jobsRefreshSignal} />
        ) : (
          <div className="space-y-4">
            {/* Search, Filter & Sort Toolbar */}
            <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-200 bg-white p-3.5 shadow-xs">
              <div className="relative min-w-[220px] flex-1">
                <Search className="pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <input
                  type="search"
                  value={searchInput}
                  onChange={(e) => setSearchInput(e.target.value)}
                  placeholder="Search tasks (min 2 chars)..."
                  className="w-full rounded-xl border border-slate-300 bg-slate-50/50 py-2 pr-3 pl-9 text-sm text-slate-900 placeholder:text-slate-400 focus:border-indigo-500 focus:bg-white focus:outline-none"
                />
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <div className="flex items-center rounded-xl bg-slate-100 p-1 text-xs font-medium">
                  {(
                    [
                      { key: "", label: "All" },
                      { key: "todo", label: "Todo" },
                      { key: "in_progress", label: "In Progress" },
                      { key: "done", label: "Done" },
                    ] as const
                  ).map((item) => (
                    <button
                      key={item.label}
                      type="button"
                      onClick={() => setStatusFilter(item.key)}
                      className={`rounded-lg px-2.5 py-1 transition ${
                        statusFilter === item.key
                          ? "bg-white text-slate-900 shadow-xs"
                          : "text-slate-600 hover:text-slate-900"
                      }`}
                    >
                      {item.label}
                    </button>
                  ))}
                </div>

                <select
                  aria-label="Sort tasks by"
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as TaskSortBy)}
                  className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-700 focus:border-indigo-500 focus:outline-none"
                >
                  <option value="created_at">Created Date</option>
                  <option value="due_at">Due Date</option>
                  <option value="title">Title</option>
                  <option value="status">Status</option>
                </select>

                <button
                  type="button"
                  onClick={() =>
                    setSortOrder((prev) => (prev === "asc" ? "desc" : "asc"))
                  }
                  title={`Sort order: ${sortOrder.toUpperCase()}`}
                  className="inline-flex items-center gap-1 rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50"
                >
                  <ArrowUpDown className="h-3.5 w-3.5" />
                  {sortOrder.toUpperCase()}
                </button>
              </div>
            </div>

            {/* Paginated Task List */}
            <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xs">
              {isLoadingTasks && !tasksPage ? (
                <div className="flex items-center justify-center py-16 text-sm text-slate-500">
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Loading tasks...
                </div>
              ) : !tasksPage || tasksPage.items.length === 0 ? (
                <div className="px-6 py-16 text-center">
                  <p className="text-sm font-medium text-slate-700">
                    No tasks found
                  </p>
                  <p className="mt-1 text-xs text-slate-500">
                    Create a new task or adjust your filters.
                  </p>
                  <button
                    type="button"
                    onClick={() => setIsCreateOpen(true)}
                    className="mt-4 inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white hover:bg-indigo-700"
                  >
                    <Plus className="h-4 w-4" />
                    Create Task
                  </button>
                </div>
              ) : (
                <>
                  <ul className="divide-y divide-slate-100">
                    {tasksPage.items.map((task) => {
                      const overdue = isOverdue(task);
                      return (
                        <li
                          key={task.id}
                          className="flex flex-wrap items-center justify-between gap-4 px-5 py-4 transition hover:bg-slate-50/80"
                        >
                          <button
                            type="button"
                            onClick={() => setSelectedTask(task)}
                            className="min-w-0 flex-1 text-left"
                          >
                            <div className="flex items-center gap-2.5">
                              <span className="truncate text-sm font-semibold text-slate-900">
                                {task.title}
                              </span>
                              <span
                                className={`shrink-0 rounded-full px-2.5 py-0.5 text-[11px] font-medium ${STATUS_BADGE[task.status]}`}
                              >
                                {STATUS_LABEL[task.status]}
                              </span>
                            </div>

                            {task.description && (
                              <p className="mt-1 line-clamp-1 text-xs text-slate-500">
                                {task.description}
                              </p>
                            )}

                            <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-slate-500">
                              {task.due_at && (
                                <span
                                  className={`inline-flex items-center gap-1 ${
                                    overdue
                                      ? "font-semibold text-rose-600"
                                      : ""
                                  }`}
                                >
                                  <Calendar className="h-3.5 w-3.5" />
                                  {overdue ? "Overdue: " : "Due: "}
                                  {new Date(task.due_at).toLocaleDateString()}
                                </span>
                              )}

                              {task.attachments.length > 0 && (
                                <span className="inline-flex items-center gap-1 text-slate-600">
                                  <Paperclip className="h-3.5 w-3.5" />
                                  {task.attachments.length}{" "}
                                  {task.attachments.length === 1
                                    ? "file"
                                    : "files"}
                                </span>
                              )}
                            </div>
                          </button>

                          <div className="flex shrink-0 items-center gap-2">
                            <select
                              aria-label={`Change status for ${task.title}`}
                              value={task.status}
                              onChange={(e) =>
                                handleQuickStatusChange(
                                  task,
                                  e.target.value as TaskStatus
                                )
                              }
                              className="rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 focus:border-indigo-500 focus:outline-none"
                            >
                              <option value="todo">Todo</option>
                              <option value="in_progress">In Progress</option>
                              <option value="done">Done</option>
                            </select>

                            <button
                              type="button"
                              onClick={() => setSelectedTask(task)}
                              className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100"
                            >
                              Open
                            </button>
                          </div>
                        </li>
                      );
                    })}
                  </ul>

                  <Pagination
                    page={tasksPage.page}
                    pageSize={tasksPage.page_size}
                    total={tasksPage.total}
                    totalPages={tasksPage.total_pages}
                    hasPrev={tasksPage.has_prev}
                    hasNext={tasksPage.has_next}
                    onPageChange={setPage}
                    onPageSizeChange={setPageSize}
                  />
                </>
              )}
            </div>
          </div>
        )}
      </main>

      <TaskModal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        onCreated={() => {
          addToast("Task created", { variant: "success" });
          void loadTasks();
        }}
      />

      <TaskDetailDrawer
        task={selectedTask}
        onClose={() => setSelectedTask(null)}
        onUpdated={(updated) => {
          setSelectedTask(updated);
          void loadTasks();
        }}
        onDeleted={() => {
          void loadTasks();
        }}
      />
    </div>
  );
}
