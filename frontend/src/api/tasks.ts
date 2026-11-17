import { apiFetchRaw, apiRequest } from "./client";
import type {
  PaginatedResponse,
  TaskCreate,
  TaskRead,
  TaskStatus,
  TaskUpdate,
} from "../types/api";

export type TaskSortBy = "created_at" | "due_at" | "title" | "status";
export type SortOrder = "asc" | "desc";

export interface FetchTasksParams {
  page?: number;
  pageSize?: number;
  status?: TaskStatus | "";
  q?: string;
  sortBy?: TaskSortBy;
  sortOrder?: SortOrder;
}

export async function fetchTasks(params: FetchTasksParams = {}): Promise<{
  data: PaginatedResponse<TaskRead>;
  cacheStatus: string | null;
}> {
  const query = new URLSearchParams();
  if (params.page) query.set("page", String(params.page));
  if (params.pageSize) query.set("page_size", String(params.pageSize));
  if (params.status) query.set("status", params.status);
  if (params.q && params.q.trim().length >= 2) {
    query.set("q", params.q.trim());
  }
  if (params.sortBy) query.set("sort_by", params.sortBy);
  if (params.sortOrder) query.set("sort_order", params.sortOrder);

  const qs = query.toString();
  const res = await apiFetchRaw(`/tasks${qs ? `?${qs}` : ""}`, {
    method: "GET",
  });
  const cacheStatus = res.headers.get("X-Cache");
  const data = (await res.json()) as PaginatedResponse<TaskRead>;
  return { data, cacheStatus };
}

export async function fetchTask(taskId: number): Promise<{
  data: TaskRead;
  cacheStatus: string | null;
}> {
  const res = await apiFetchRaw(`/tasks/${taskId}`, { method: "GET" });
  const cacheStatus = res.headers.get("X-Cache");
  const data = (await res.json()) as TaskRead;
  return { data, cacheStatus };
}

export async function createTask(payload: TaskCreate): Promise<TaskRead> {
  return apiRequest<TaskRead>("/tasks", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateTask(
  taskId: number,
  payload: TaskUpdate
): Promise<TaskRead> {
  return apiRequest<TaskRead>(`/tasks/${taskId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function deleteTask(taskId: number): Promise<void> {
  return apiRequest<void>(`/tasks/${taskId}`, {
    method: "DELETE",
  });
}
