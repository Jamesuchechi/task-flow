export type TaskStatus = "todo" | "in_progress" | "done";

export type JobStatus = "pending" | "running" | "completed" | "failed";
export type JobType = "export_tasks" | "overdue_digest";

export interface UserRead {
  id: number;
  username: string;
  email: string;
  role: string;
  created_at: string;
}

export interface Token {
  access_token: string;
  refresh_token?: string | null;
  token_type: string;
}

export interface AttachmentRead {
  id: number;
  task_id: number;
  owner_id: number;
  filename: string;
  content_type: string;
  size_bytes: number;
  created_at: string;
}

export interface TaskRead {
  id: number;
  owner_id: number;
  title: string;
  description: string | null;
  status: TaskStatus;
  due_at: string | null;
  created_at: string;
  attachments: AttachmentRead[];
}

export interface TaskCreate {
  title: string;
  description?: string | null;
  status?: TaskStatus;
  due_at?: string | null;
}

export interface TaskUpdate {
  title?: string | null;
  description?: string | null;
  status?: TaskStatus | null;
  due_at?: string | null;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface JobRead {
  id: string;
  job_type: JobType;
  status: JobStatus;
  payload: Record<string, unknown> | null;
  result: Record<string, unknown> | null;
  error: string | null;
  owner_id: number;
  created_at: string;
  completed_at: string | null;
}

export interface HealthResponse {
  status: string;
  message: string;
  cache: {
    backend: string;
    keys: number;
    hits: number;
    misses: number;
    hit_rate_percent: number;
  };
  websocket_connections: number;
}

export interface WsEventMessage {
  event: string;
  data?: Record<string, unknown>;
  timestamp?: string;
  user_id?: number;
  username?: string;
  message?: string;
}
