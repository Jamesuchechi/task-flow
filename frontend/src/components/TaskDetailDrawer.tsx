import { useEffect, useRef, useState, type FormEvent } from "react";
import {
  Download,
  FileText,
  Loader2,
  Paperclip,
  Trash2,
  Upload,
  X,
} from "lucide-react";
import {
  deleteAttachment,
  downloadAttachment,
  listTaskAttachments,
  uploadAttachment,
  validateAttachmentFile,
} from "../api/attachments";
import { ApiError } from "../api/client";
import { deleteTask, updateTask } from "../api/tasks";
import { useToast } from "../context/ToastContext";
import type { AttachmentRead, TaskRead, TaskStatus } from "../types/api";

interface TaskDetailDrawerProps {
  task: TaskRead | null;
  onClose: () => void;
  onUpdated: (task: TaskRead) => void;
  onDeleted: (taskId: number) => void;
}

function toDatetimeLocal(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(
    d.getHours()
  )}:${pad(d.getMinutes())}`;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function TaskDetailDrawer({
  task,
  onClose,
  onUpdated,
  onDeleted,
}: TaskDetailDrawerProps) {
  const { addToast } = useToast();
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [status, setStatus] = useState<TaskStatus>("todo");
  const [dueAt, setDueAt] = useState("");
  const [attachments, setAttachments] = useState<AttachmentRead[]>([]);
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  useEffect(() => {
    if (!task) return;
    setTitle(task.title);
    setDescription(task.description ?? "");
    setStatus(task.status);
    setDueAt(toDatetimeLocal(task.due_at));
    setAttachments(task.attachments ?? []);
    setConfirmDelete(false);

    listTaskAttachments(task.id)
      .then(setAttachments)
      .catch(() => {
        // Fallback to task.attachments already set
      });
  }, [task]);

  if (!task) return null;

  async function handleSave(e: FormEvent) {
    e.preventDefault();
    if (!task) return;
    if (!title.trim()) {
      addToast("Title cannot be empty", { variant: "error" });
      return;
    }

    setIsSaving(true);
    try {
      const updated = await updateTask(task.id, {
        title: title.trim(),
        description: description.trim() || null,
        status,
        due_at: dueAt ? new Date(dueAt).toISOString() : null,
      });
      onUpdated(updated);
      addToast("Task updated", { variant: "success" });
    } catch (err) {
      addToast(
        err instanceof ApiError ? err.message : "Failed to update task",
        { variant: "error" }
      );
    } finally {
      setIsSaving(false);
    }
  }

  async function handleDeleteTask() {
    if (!task) return;
    setIsDeleting(true);
    try {
      await deleteTask(task.id);
      onDeleted(task.id);
      onClose();
      addToast("Task deleted", { variant: "info" });
    } catch (err) {
      addToast(
        err instanceof ApiError ? err.message : "Failed to delete task",
        { variant: "error" }
      );
    } finally {
      setIsDeleting(false);
    }
  }

  async function handleFileSelect(file: File | undefined) {
    if (!file || !task) return;
    const validationErr = validateAttachmentFile(file);
    if (validationErr) {
      addToast("Invalid file", { message: validationErr, variant: "error" });
      return;
    }

    setIsUploading(true);
    try {
      const created = await uploadAttachment(task.id, file);
      setAttachments((prev) => [created, ...prev]);
      addToast("File uploaded", {
        message: created.filename,
        variant: "success",
      });
    } catch (err) {
      addToast(
        err instanceof ApiError ? err.message : "Failed to upload file",
        { variant: "error" }
      );
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  }

  async function handleDeleteAttachment(att: AttachmentRead) {
    try {
      await deleteAttachment(att.id);
      setAttachments((prev) => prev.filter((item) => item.id !== att.id));
      addToast("Attachment removed", {
        message: att.filename,
        variant: "info",
      });
    } catch (err) {
      addToast(
        err instanceof ApiError ? err.message : "Failed to delete attachment",
        { variant: "error" }
      );
    }
  }

  async function handleDownload(att: AttachmentRead) {
    try {
      await downloadAttachment(att.id, att.filename);
    } catch (err) {
      addToast(
        err instanceof ApiError ? err.message : "Download failed",
        { variant: "error" }
      );
    }
  }

  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-slate-900/30 backdrop-blur-xs">
      <div className="flex h-full w-full max-w-lg flex-col border-l border-slate-200 bg-white shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
          <div>
            <span className="text-xs font-medium text-slate-400">
              Task #{task.id}
            </span>
            <h2 className="text-lg font-semibold text-slate-900">
              Task Details
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close drawer"
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 space-y-6 overflow-y-auto p-6">
          <form onSubmit={handleSave} className="space-y-4">
            <div>
              <label
                htmlFor="detail-title"
                className="block text-sm font-medium text-slate-700"
              >
                Title
              </label>
              <input
                id="detail-title"
                type="text"
                required
                maxLength={120}
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="mt-1.5 block w-full rounded-xl border border-slate-300 px-3.5 py-2 text-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 focus:outline-none"
              />
            </div>

            <div>
              <label
                htmlFor="detail-desc"
                className="block text-sm font-medium text-slate-700"
              >
                Description
              </label>
              <textarea
                id="detail-desc"
                rows={4}
                maxLength={2000}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Add notes or details..."
                className="mt-1.5 block w-full rounded-xl border border-slate-300 px-3.5 py-2 text-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 focus:outline-none"
              />
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label
                  htmlFor="detail-status"
                  className="block text-sm font-medium text-slate-700"
                >
                  Status
                </label>
                <select
                  id="detail-status"
                  value={status}
                  onChange={(e) => setStatus(e.target.value as TaskStatus)}
                  className="mt-1.5 block w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2 text-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 focus:outline-none"
                >
                  <option value="todo">Todo</option>
                  <option value="in_progress">In Progress</option>
                  <option value="done">Done</option>
                </select>
              </div>

              <div>
                <label
                  htmlFor="detail-due"
                  className="block text-sm font-medium text-slate-700"
                >
                  Due Date
                </label>
                <input
                  id="detail-due"
                  type="datetime-local"
                  value={dueAt}
                  onChange={(e) => setDueAt(e.target.value)}
                  className="mt-1.5 block w-full rounded-xl border border-slate-300 px-3.5 py-2 text-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 focus:outline-none"
                />
              </div>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
              {!confirmDelete ? (
                <button
                  type="button"
                  onClick={() => setConfirmDelete(true)}
                  className="inline-flex items-center gap-1.5 rounded-xl border border-rose-200 bg-rose-50 px-3.5 py-2 text-sm font-medium text-rose-700 hover:bg-rose-100"
                >
                  <Trash2 className="h-4 w-4" />
                  Delete Task
                </button>
              ) : (
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    disabled={isDeleting}
                    onClick={handleDeleteTask}
                    className="inline-flex items-center gap-1.5 rounded-xl bg-rose-600 px-3.5 py-2 text-sm font-semibold text-white hover:bg-rose-700 disabled:opacity-60"
                  >
                    {isDeleting && (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    )}
                    Confirm Delete
                  </button>
                  <button
                    type="button"
                    onClick={() => setConfirmDelete(false)}
                    className="rounded-xl px-2.5 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100"
                  >
                    Cancel
                  </button>
                </div>
              )}

              <button
                type="submit"
                disabled={isSaving}
                className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 disabled:opacity-60"
              >
                {isSaving && <Loader2 className="h-4 w-4 animate-spin" />}
                Save Changes
              </button>
            </div>
          </form>

          {/* Attachments Section */}
          <div className="border-t border-slate-200 pt-5">
            <div className="flex items-center justify-between">
              <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                <Paperclip className="h-4 w-4 text-slate-500" />
                Attachments ({attachments.length})
              </h3>

              <input
                ref={fileInputRef}
                type="file"
                className="hidden"
                onChange={(e) => handleFileSelect(e.target.files?.[0])}
              />
              <button
                type="button"
                disabled={isUploading}
                onClick={() => fileInputRef.current?.click()}
                className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-60"
              >
                {isUploading ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Upload className="h-3.5 w-3.5" />
                )}
                {isUploading ? "Uploading..." : "Upload File"}
              </button>
            </div>

            <p className="mt-1 text-xs text-slate-500">
              Max 10 MB • .txt, .md, .pdf, .png, .jpg, .gif, .csv, .json, .zip
            </p>

            {attachments.length === 0 ? (
              <div className="mt-4 rounded-xl border border-dashed border-slate-200 bg-slate-50 p-5 text-center text-xs text-slate-500">
                No files attached to this task yet.
              </div>
            ) : (
              <ul className="mt-3 space-y-2">
                {attachments.map((att) => (
                  <li
                    key={att.id}
                    className="flex items-center justify-between gap-3 rounded-xl border border-slate-200 bg-slate-50/60 px-3.5 py-2.5"
                  >
                    <div className="flex min-w-0 items-center gap-2.5">
                      <FileText className="h-4 w-4 shrink-0 text-indigo-600" />
                      <div className="min-w-0">
                        <p className="truncate text-sm font-medium text-slate-800">
                          {att.filename}
                        </p>
                        <p className="text-xs text-slate-500">
                          {formatBytes(att.size_bytes)}
                        </p>
                      </div>
                    </div>

                    <div className="flex shrink-0 items-center gap-1">
                      <button
                        type="button"
                        onClick={() => handleDownload(att)}
                        title="Download file"
                        className="rounded-lg p-1.5 text-slate-600 hover:bg-white hover:text-indigo-600"
                      >
                        <Download className="h-4 w-4" />
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDeleteAttachment(att)}
                        title="Delete file"
                        className="rounded-lg p-1.5 text-slate-500 hover:bg-white hover:text-rose-600"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
