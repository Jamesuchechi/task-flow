import { useState, type FormEvent } from "react";
import { Loader2, X } from "lucide-react";
import { ApiError } from "../api/client";
import { createTask } from "../api/tasks";
import type { TaskRead, TaskStatus } from "../types/api";

interface TaskModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated: (task: TaskRead) => void;
}

export function TaskModal({ isOpen, onClose, onCreated }: TaskModalProps) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [status, setStatus] = useState<TaskStatus>("todo");
  const [dueAt, setDueAt] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen) return null;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);

    if (!title.trim()) {
      setError("Title is required.");
      return;
    }

    setIsSubmitting(true);
    try {
      const created = await createTask({
        title: title.trim(),
        description: description.trim() || null,
        status,
        due_at: dueAt ? new Date(dueAt).toISOString() : null,
      });
      setTitle("");
      setDescription("");
      setStatus("todo");
      setDueAt("");
      onCreated(created);
      onClose();
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Failed to create task."
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4 backdrop-blur-xs"
      role="dialog"
      aria-modal="true"
      aria-labelledby="create-task-title"
    >
      <div className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-6 shadow-xl">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <h2
            id="create-task-title"
            className="text-lg font-semibold text-slate-900"
          >
            Create New Task
          </h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close modal"
            className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {error && (
          <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 px-3.5 py-2.5 text-sm text-rose-800">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          <div>
            <label
              htmlFor="new-task-title"
              className="block text-sm font-medium text-slate-700"
            >
              Title
            </label>
            <input
              id="new-task-title"
              type="text"
              required
              maxLength={120}
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g., Prepare project presentation"
              className="mt-1.5 block w-full rounded-xl border border-slate-300 px-3.5 py-2 text-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 focus:outline-none"
            />
          </div>

          <div>
            <label
              htmlFor="new-task-desc"
              className="block text-sm font-medium text-slate-700"
            >
              Description
            </label>
            <textarea
              id="new-task-desc"
              rows={3}
              maxLength={2000}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optional details..."
              className="mt-1.5 block w-full rounded-xl border border-slate-300 px-3.5 py-2 text-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 focus:outline-none"
            />
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label
                htmlFor="new-task-status"
                className="block text-sm font-medium text-slate-700"
              >
                Status
              </label>
              <select
                id="new-task-status"
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
                htmlFor="new-task-due"
                className="block text-sm font-medium text-slate-700"
              >
                Due Date
              </label>
              <input
                id="new-task-due"
                type="datetime-local"
                value={dueAt}
                onChange={(e) => setDueAt(e.target.value)}
                className="mt-1.5 block w-full rounded-xl border border-slate-300 px-3.5 py-2 text-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 focus:outline-none"
              />
            </div>
          </div>

          <div className="flex items-center justify-end gap-2.5 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 disabled:opacity-60"
            >
              {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
              Create Task
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
