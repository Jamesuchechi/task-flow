import { useCallback, useEffect, useState } from "react";
import {
  Clock,
  Download,
  FileSpreadsheet,
  Loader2,
  RefreshCw,
} from "lucide-react";
import { ApiError } from "../api/client";
import {
  downloadJobExport,
  enqueueExportTasks,
  enqueueOverdueDigest,
  fetchJobs,
} from "../api/jobs";
import { useToast } from "../context/ToastContext";
import type {
  JobRead,
  JobStatus,
  PaginatedResponse,
  TaskStatus,
} from "../types/api";
import { Pagination } from "./Pagination";

interface JobsPanelProps {
  refreshSignal: number;
}

const JOB_STATUS_BADGE: Record<JobStatus, string> = {
  pending: "bg-slate-100 text-slate-700",
  running: "bg-amber-50 text-amber-700",
  completed: "bg-emerald-50 text-emerald-700",
  failed: "bg-rose-50 text-rose-700",
};

export function JobsPanel({ refreshSignal }: JobsPanelProps) {
  const { addToast } = useToast();

  const [jobsPage, setJobsPage] = useState<PaginatedResponse<JobRead> | null>(
    null
  );
  const [page, setPage] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [exportFormat, setExportFormat] = useState<"json" | "csv">("json");
  const [exportStatus, setExportStatus] = useState<TaskStatus | "">("");
  const [isQueueingExport, setIsQueueingExport] = useState(false);
  const [isQueueingDigest, setIsQueueingDigest] = useState(false);

  const loadJobs = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await fetchJobs(page, 10);
      setJobsPage(data);
    } catch (err) {
      addToast(
        err instanceof ApiError ? err.message : "Failed to load jobs",
        { variant: "error" }
      );
    } finally {
      setIsLoading(false);
    }
  }, [page, addToast]);

  useEffect(() => {
    void loadJobs();
  }, [loadJobs, refreshSignal]);

  async function handleExport() {
    setIsQueueingExport(true);
    try {
      await enqueueExportTasks(exportFormat, exportStatus);
      addToast("Export job queued", {
        message: `Generating ${exportFormat.toUpperCase()} export...`,
        variant: "info",
      });
      setPage(1);
      await loadJobs();
    } catch (err) {
      addToast(
        err instanceof ApiError ? err.message : "Failed to queue export",
        { variant: "error" }
      );
    } finally {
      setIsQueueingExport(false);
    }
  }

  async function handleDigest() {
    setIsQueueingDigest(true);
    try {
      await enqueueOverdueDigest();
      addToast("Overdue digest queued", {
        message: "Scanning your tasks...",
        variant: "info",
      });
      setPage(1);
      await loadJobs();
    } catch (err) {
      addToast(
        err instanceof ApiError ? err.message : "Failed to queue digest",
        { variant: "error" }
      );
    } finally {
      setIsQueueingDigest(false);
    }
  }

  async function handleDownloadExport(job: JobRead) {
    const filename =
      typeof job.result?.filename === "string"
        ? job.result.filename
        : `tasks_export_${job.id}.json`;
    try {
      await downloadJobExport(job.id, filename);
    } catch (err) {
      addToast(
        err instanceof ApiError ? err.message : "Failed to download export",
        { variant: "error" }
      );
    }
  }

  return (
    <div className="space-y-6">
      {/* Action Cards */}
      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600">
              <FileSpreadsheet className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-900">
                Export Tasks
              </h3>
              <p className="text-xs text-slate-500">
                Queue an asynchronous JSON or CSV export
              </p>
            </div>
          </div>

          <div className="mt-4 flex flex-wrap items-center gap-2.5">
            <select
              value={exportFormat}
              onChange={(e) =>
                setExportFormat(e.target.value as "json" | "csv")
              }
              className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-700 focus:border-indigo-500 focus:outline-none"
            >
              <option value="json">JSON</option>
              <option value="csv">CSV</option>
            </select>

            <select
              value={exportStatus}
              onChange={(e) =>
                setExportStatus(e.target.value as TaskStatus | "")
              }
              className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-700 focus:border-indigo-500 focus:outline-none"
            >
              <option value="">All Statuses</option>
              <option value="todo">Todo</option>
              <option value="in_progress">In Progress</option>
              <option value="done">Done</option>
            </select>

            <button
              type="button"
              disabled={isQueueingExport}
              onClick={handleExport}
              className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white hover:bg-indigo-700 disabled:opacity-60"
            >
              {isQueueingExport && (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              )}
              Start Export
            </button>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-amber-50 text-amber-600">
              <Clock className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-900">
                Overdue Digest
              </h3>
              <p className="text-xs text-slate-500">
                Scan your tasks for overdue and upcoming deadlines
              </p>
            </div>
          </div>

          <div className="mt-4">
            <button
              type="button"
              disabled={isQueueingDigest}
              onClick={handleDigest}
              className="inline-flex items-center gap-1.5 rounded-xl border border-slate-300 bg-white px-4 py-2 text-xs font-semibold text-slate-800 hover:bg-slate-50 disabled:opacity-60"
            >
              {isQueueingDigest && (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              )}
              Run Overdue Digest
            </button>
          </div>
        </div>
      </div>

      {/* Job History */}
      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xs">
        <div className="flex items-center justify-between border-b border-slate-200 px-5 py-3.5">
          <h3 className="text-sm font-semibold text-slate-900">
            Background Job History
          </h3>
          <button
            type="button"
            onClick={() => void loadJobs()}
            className="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-medium text-slate-600 hover:bg-slate-100"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh
          </button>
        </div>

        {isLoading && !jobsPage ? (
          <div className="flex items-center justify-center py-12 text-sm text-slate-500">
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Loading jobs...
          </div>
        ) : !jobsPage || jobsPage.items.length === 0 ? (
          <div className="py-12 text-center text-sm text-slate-500">
            No background jobs yet. Trigger an export or overdue digest above.
          </div>
        ) : (
          <>
            <ul className="divide-y divide-slate-100">
              {jobsPage.items.map((job) => {
                const isExportReady =
                  job.job_type === "export_tasks" &&
                  job.status === "completed";
                const isDigestReady =
                  job.job_type === "overdue_digest" &&
                  job.status === "completed" &&
                  job.result;

                return (
                  <li
                    key={job.id}
                    className="flex flex-wrap items-center justify-between gap-4 px-5 py-4"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2.5">
                        <span className="text-sm font-medium text-slate-900">
                          {job.job_type === "export_tasks"
                            ? "Export Tasks"
                            : "Overdue Digest"}
                        </span>
                        <span
                          className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${JOB_STATUS_BADGE[job.status]}`}
                        >
                          {job.status}
                        </span>
                      </div>

                      <p className="text-xs text-slate-500">
                        Created {new Date(job.created_at).toLocaleString()}
                        {job.job_type === "export_tasks" &&
                          job.result &&
                          typeof job.result.task_count === "number" && (
                            <>
                              {" "}
                              • {job.result.task_count} tasks (
                              {String(job.result.format).toUpperCase()})
                            </>
                          )}
                      </p>

                      {isDigestReady && job.result && (
                        <p className="text-xs font-medium text-slate-700">
                          Overdue:{" "}
                          <span className="text-rose-600">
                            {String(job.result.overdue_count ?? 0)}
                          </span>{" "}
                          • Upcoming:{" "}
                          <span className="text-indigo-600">
                            {String(job.result.upcoming_count ?? 0)}
                          </span>
                        </p>
                      )}

                      {job.error && (
                        <p className="text-xs text-rose-600">{job.error}</p>
                      )}
                    </div>

                    {isExportReady && (
                      <button
                        type="button"
                        onClick={() => handleDownloadExport(job)}
                        className="inline-flex items-center gap-1.5 rounded-xl border border-indigo-200 bg-indigo-50 px-3.5 py-1.5 text-xs font-semibold text-indigo-700 hover:bg-indigo-100"
                      >
                        <Download className="h-3.5 w-3.5" />
                        Download
                      </button>
                    )}
                  </li>
                );
              })}
            </ul>

            <Pagination
              page={jobsPage.page}
              pageSize={jobsPage.page_size}
              total={jobsPage.total}
              totalPages={jobsPage.total_pages}
              hasPrev={jobsPage.has_prev}
              hasNext={jobsPage.has_next}
              onPageChange={setPage}
            />
          </>
        )}
      </div>
    </div>
  );
}
