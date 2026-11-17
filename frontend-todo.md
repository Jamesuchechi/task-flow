# TaskFlow Frontend Todo

A complete checklist of all planned features, requirements, and components for the **React + Vite + TypeScript + Tailwind CSS** frontend.

---

## 1. Project Setup & Core Infrastructure
- [ ] Scaffold `frontend/` with Vite + React + TypeScript
- [ ] Configure Tailwind CSS and base design system (colors, status badges, typography)
- [ ] Install `react-router-dom` and icon library (`lucide-react`)
- [ ] Add `frontend/.env` (`VITE_API_BASE_URL=http://127.0.0.1:8000`) and `.env.example`
- [ ] Define TypeScript interfaces in `src/types/api.ts` matching backend Pydantic schemas (`UserRead`, `Token`, `TaskRead`, `TaskCreate`, `TaskUpdate`, `PaginatedResponse`, `AttachmentRead`, `JobRead`, `AppError`)
- [ ] Build unified API client in `src/api/client.ts`:
  - [ ] Attach `Authorization: Bearer <access_token>` header
  - [ ] Automatic `POST /auth/refresh` retry on `401` responses
  - [ ] Normalize backend `AppError` (`error.code`, `error.message`) and FastAPI `detail` errors
  - [ ] Handle `429 Too Many Requests` rate-limit errors gracefully
- [ ] Implement `AuthContext.tsx` (login, register, logout, `GET /auth/me` hydration, token storage)
- [ ] Implement `ProtectedRoute.tsx` (redirect unauthenticated users to `/login`, redirect authenticated users away from `/login` and `/register`)
- [ ] Implement `ToastContainer.tsx` for real-time WebSocket & API notifications

---

## 2. Landing Page (`/`)
- [ ] Top navbar with TaskFlow logo, live API status badge (`GET /health`), and auth-aware CTAs (**Sign In** / **Get Started** or **Go to Dashboard**)
- [ ] Hero section with headline, value proposition, and primary CTAs
- [ ] 4-card feature showcase (Search & Pagination, File Attachments, Background Jobs & Exports, Real-Time WebSockets)
- [ ] Responsive layout for desktop and mobile

---

## 3. Authentication Pages (`/login`, `/register`)
- [ ] **Register Page (`/register`):**
  - [ ] Fields: `username` (3–50 chars), `email` (valid email), `password` (8–128 chars)
  - [ ] Client-side validation & server error banner (`409` duplicate user/email, `429` rate limit)
  - [ ] Loading state on submit and redirect to `/login` on success
- [ ] **Login Page (`/login`):**
  - [ ] Fields: `username`, `password`
  - [ ] Submit `application/x-www-form-urlencoded` to `POST /auth/login`
  - [ ] Store `access_token` + `refresh_token`, fetch `/auth/me`, redirect to `/dashboard`
  - [ ] Clear error display for `401` invalid credentials and `429` rate limit

---

## 4. Dashboard (`/dashboard`)

### A. Top Bar & Navigation
- [ ] TaskFlow logo + `Tasks` / `Background Jobs` tab switcher
- [ ] Real-time WebSocket status pill (`Live` / `Reconnecting`)
- [ ] Cache indicator badge (`X-Cache: HIT | MISS`) from latest task fetch
- [ ] `+ New Task` primary button
- [ ] User menu showing `username` and **Logout** button (clears tokens & closes WebSocket)

### B. Task List, Filtering, Sorting & Pagination (`GET /tasks`)
- [ ] Debounced search input (`q`, minimum 2 characters, ~300ms debounce via `useDebounce.ts`)
- [ ] Status filter tabs (`All`, `todo`, `in_progress`, `done`)
- [ ] Sort selector (`created_at`, `due_at`, `title`, `status`) + ascending/descending toggle
- [ ] Task cards/rows showing title, status badge, due date (with overdue highlight), and attachment count
- [ ] Quick status update dropdown directly from task row (`PATCH /tasks/{id}`)
- [ ] `Pagination.tsx` component (`page`, `page_size`, `total`, `total_pages`, `has_prev`, `has_next`)
- [ ] Loading skeleton/spinner and empty state UI

### C. Task CRUD & Detail Drawer
- [ ] `TaskModal.tsx` for creating a new task (`POST /tasks`: `title`, `description`, `status`, `due_at`)
- [ ] `TaskDetailDrawer.tsx` for viewing & editing a task (`GET /tasks/{id}`, `PATCH /tasks/{id}`)
- [ ] Delete task with confirmation prompt (`DELETE /tasks/{id}`)

### D. File Attachments (`/tasks/{id}/attachments`, `/attachments/{id}/*`)
- [ ] File picker / drag-and-drop upload inside `TaskDetailDrawer.tsx` (`POST /tasks/{id}/attachments`)
- [ ] Client-side pre-validation for allowed extensions (`.txt`, `.md`, `.pdf`, `.png`, `.jpg`, `.jpeg`, `.gif`, `.csv`, `.json`, `.zip`) and max size (10 MB)
- [ ] Attachment list showing filename, file size, and upload date (`GET /tasks/{id}/attachments`)
- [ ] Authenticated Blob download button (`GET /attachments/{id}/download`)
- [ ] Delete attachment with confirmation (`DELETE /attachments/{id}`)

### E. Background Jobs & Exports (`JobsPanel.tsx`)
- [ ] Trigger **Export Tasks** (`POST /jobs/export-tasks`) with format selector (`json` / `csv`) and optional status filter
- [ ] Trigger **Overdue Digest** (`POST /jobs/overdue-digest`)
- [ ] Paginated jobs history list (`GET /jobs`) showing `job_type`, `status` (`pending`, `running`, `completed`, `failed`), and timestamps
- [ ] Display Overdue Digest summary (`overdue_count`, `upcoming_count`, overdue task list)
- [ ] Authenticated Blob **Download** button for completed export jobs (`GET /jobs/{id}/download`)

### F. Real-Time WebSockets (`useWebSocket.ts`)
- [ ] Connect to `WS /ws/tasks?token=<access_token>` on dashboard mount
- [ ] Periodic `ping` / `pong` heartbeat and automatic reconnect with backoff
- [ ] Handle events (`task.created`, `task.updated`, `task.deleted`, `attachment.uploaded`, `attachment.deleted`, `job.completed`, `job.failed`) to refresh data and show toast notifications

---

## 5. Verification & Quality Checks
- [ ] Verify TypeScript compilation (`npm run build` / `tsc --noEmit`) with zero errors
- [ ] Verify all frontend flows end-to-end against the running FastAPI backend:
  - [ ] Landing page & `/health` indicator
  - [ ] Register, Login, Token Refresh, Protected Routes, Logout
  - [ ] Task Create, Paginated List, Search/Filter/Sort, Cache `HIT`/`MISS`, Update, Delete
  - [ ] File Upload, Download, Delete
  - [ ] Background Export (JSON/CSV) & Overdue Digest + Download
  - [ ] Real-time WebSocket events & notifications
