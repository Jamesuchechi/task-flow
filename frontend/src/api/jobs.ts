import { apiRequest, downloadProtectedFile } from "./client";
import type { JobRead, PaginatedResponse, TaskStatus } from "../types/api";

export async function enqueueExportTasks(
  format: "json" | "csv" = "json",
  status?: TaskStatus | ""
): Promise<JobRead> {
  return apiRequest<JobRead>("/jobs/export-tasks", {
    method: "POST",
    body: JSON.stringify({
      format,
      status: status || null,
    }),
  });
}

export async function enqueueOverdueDigest(): Promise<JobRead> {
  return apiRequest<JobRead>("/jobs/overdue-digest", {
    method: "POST",
  });
}

export async function fetchJobs(
  page = 1,
  pageSize = 10
): Promise<PaginatedResponse<JobRead>> {
  return apiRequest<PaginatedResponse<JobRead>>(
    `/jobs?page=${page}&page_size=${pageSize}`,
    { method: "GET" }
  );
}

export async function fetchJob(jobId: string): Promise<JobRead> {
  return apiRequest<JobRead>(`/jobs/${jobId}`, { method: "GET" });
}

export async function downloadJobExport(
  jobId: string,
  filename: string
): Promise<void> {
  await downloadProtectedFile(`/jobs/${jobId}/download`, filename);
}
