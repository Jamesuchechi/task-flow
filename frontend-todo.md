# TaskFlow Frontend Todo

A complete checklist of all planned features, requirements, and components for the **React + Vite + TypeScript + Tailwind CSS** frontend.

---

## 1. Project Setup & Core Infrastructure
- [x] Scaffold `frontend/` with Vite + React + TypeScript
- [x] Configure Tailwind CSS and base design system (colors, status badges, typography)
- [x] Install `react-router-dom` and icon library (`lucide-react`)
- [x] Add `frontend/.env` (`VITE_API_BASE_URL=http://127.0.0.1:8000`) and `.env.example`
- [x] Define TypeScript interfaces in `src/types/api.ts` matching backend Pydantic schemas (`UserRead`, `Token`, `TaskRead`, `TaskCreate`, `TaskUpdate`, `PaginatedResponse`, `AttachmentRead`, `JobRead`, `AppError`)
- [x] Build unified API client in `src/api/client.ts`:
  - [x] Attach `Authorization: Bearer <access_token>` header
  - [x] Automatic `POST /auth/refresh` retry on `401` responses
  - [x] Normalize backend `AppError` (`error.code`, `error.message`) and FastAPI `detail` errors
  - [x] Handle `429 Too Many Requests` rate-limit errors gracefully
- [x] Implement `AuthContext.tsx` (login, register, logout, `GET /auth/me` hydration, token storage)
- [x] Implement `ProtectedRoute.tsx` (redirect unauthenticated users to `/login`, redirect authenticated users away from `/login` and `/register`)
- [x] Implement `ToastContainer.tsx` for real-time WebSocket & API notifications

---

## 2. Landing Page (`/`)
- [x] Top navbar with TaskFlow logo, live API status badge (`GET /health`), and auth-aware CTAs (**Sign In** / **Get Started** or **Go to Dashboard**)
- [x] Hero section with headline, value proposition, and primary CTAs
- [x] 4-card feature showcase (Search & Pagination, File Attachments, Background Jobs & Exports, Real-Time WebSockets)
- [x] Responsive layout for desktop and mobile

---

## 3. Authentication Pages (`/login`, `/register`)
- [x] **Register Page (`/register`):**
  - [x] Fields: `username` (3–50 chars), `email` (valid email), `password` (8–128 chars)
  - [x] Client-side validation & server error banner (`409` duplicate user/email, `429` rate limit)
  - [x] Loading state on submit and redirect to `/login` on success
- [x] **Login Page (`/login`):**
  - [x] Fields: `username`, `password`
  - [x] Submit `application/x-www-form-urlencoded` to `POST /auth/login`
  - [x] Store `access_token` + `refresh_token`, fetch `/auth/me`, redirect to `/dashboard`
  - [x] Clear error display for `401` invalid credentials and `429` rate limit

---

## 4. Dashboard (`/dashboard`)

### A. Top Bar & Navigation
- [x] TaskFlow logo + `Tasks` / `Background Jobs` tab switcher
- [x] Real-time WebSocket status pill (`Live` / `Reconnecting`)
- [x] Cache indicator badge (`X-Cache: HIT | MISS`) from latest task fetch
- [x] `+ New Task` primary button
- [x] User menu showing `username` and **Logout** button (clears tokens & closes WebSocket)

### B. Task List, Filtering, Sorting & Pagination (`GET /tasks`)
- [x] Debounced search input (`q`, minimum 2 characters, ~300ms debounce via `useDebounce.ts`)
- [x] Status filter tabs (`All`, `todo`, `in_progress`, `done`)
- [x] Sort selector (`created_at`, `due_at`, `title`, `status`) + ascending/descending toggle
- [x] Task cards/rows showing title, status badge, due date (with overdue highlight), and attachment count
- [x] Quick status update dropdown directly from task row (`PATCH /tasks/{id}`)
- [x] `Pagination.tsx` component (`page`, `page_size`, `total`, `total_pages`, `has_prev`, `has_next`)
- [x] Loading skeleton/spinner and empty state UI

### C. Task CRUD & Detail Drawer
- [x] `TaskModal.tsx` for creating a new task (`POST /tasks`: `title`, `description`, `status`, `due_at`)
- [x] `TaskDetailDrawer.tsx` for viewing & editing a task (`GET /tasks/{id}`, `PATCH /tasks/{id}`)
- [x] Delete task with confirmation prompt (`DELETE /tasks/{id}`)

### D. File Attachments (`/tasks/{id}/attachments`, `/attachments/{id}/*`)
- [x] File picker / drag-and-drop upload inside `TaskDetailDrawer.tsx` (`POST /tasks/{id}/attachments`)
- [x] Client-side pre-validation for allowed extensions (`.txt`, `.md`, `.pdf`, `.png`, `.jpg`, `.jpeg`, `.gif`, `.csv`, `.json`, `.zip`) and max size (10 MB)
- [x] Attachment list showing filename, file size, and upload date (`GET /tasks/{id}/attachments`)
- [x] Authenticated Blob download button (`GET /attachments/{id}/download`)
- [x] Delete attachment with confirmation (`DELETE /attachments/{id}`)

### E. Background Jobs & Exports (`JobsPanel.tsx`)
- [x] Trigger **Export Tasks** (`POST /jobs/export-tasks`) with format selector (`json` / `csv`) and optional status filter
- [x] Trigger **Overdue Digest** (`POST /jobs/overdue-digest`)
- [x] Paginated jobs history list (`GET /jobs`) showing `job_type`, `status` (`pending`, `running`, `completed`, `failed`), and timestamps
- [x] Display Overdue Digest summary (`overdue_count`, `upcoming_count`, overdue task list)
- [x] Authenticated Blob **Download** button for completed export jobs (`GET /jobs/{id}/download`)

### F. Real-Time WebSockets (`useWebSocket.ts`)
- [x] Connect to `WS /ws/tasks?token=<access_token>` on dashboard mount
- [x] Periodic `ping` / `pong` heartbeat and automatic reconnect with backoff
- [x] Handle events (`task.created`, `task.updated`, `task.deleted`, `attachment.uploaded`, `attachment.deleted`, `job.completed`, `job.failed`) to refresh data and show toast notifications

---

## 5. Verification & Quality Checks
- [x] Verify TypeScript compilation (`npm run build` / `tsc --noEmit`) with zero errors
- [ ] Verify all frontend flows end-to-end against the running FastAPI backend:
  - [ ] Landing page & `/health` indicator
  - [ ] Register, Login, Token Refresh, Protected Routes, Logout
  - [ ] Task Create, Paginated List, Search/Filter/Sort, Cache `HIT`/`MISS`, Update, Delete
  - [ ] File Upload, Download, Delete
  - [ ] Background Export (JSON/CSV) & Overdue Digest + Download
  - [ ] Real-time WebSocket events & notifications
