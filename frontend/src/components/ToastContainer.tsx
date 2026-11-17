import { AlertCircle, CheckCircle2, Info, X, AlertTriangle } from "lucide-react";
import { useToast, type ToastVariant } from "../context/ToastContext";

const VARIANT_STYLES: Record<ToastVariant, string> = {
  info: "border-slate-200 bg-white text-slate-800",
  success: "border-emerald-200 bg-emerald-50 text-emerald-900",
  warning: "border-amber-200 bg-amber-50 text-amber-900",
  error: "border-rose-200 bg-rose-50 text-rose-900",
};

function ToastIcon({ variant }: { variant: ToastVariant }) {
  switch (variant) {
    case "success":
      return <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />;
    case "warning":
      return <AlertTriangle className="h-4 w-4 shrink-0 text-amber-600" />;
    case "error":
      return <AlertCircle className="h-4 w-4 shrink-0 text-rose-600" />;
    default:
      return <Info className="h-4 w-4 shrink-0 text-indigo-600" />;
  }
}

export function ToastContainer() {
  const { toasts, removeToast } = useToast();

  if (toasts.length === 0) return null;

  return (
    <div
      aria-live="polite"
      className="pointer-events-none fixed right-4 bottom-4 z-50 flex w-full max-w-sm flex-col gap-2"
    >
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`pointer-events-auto flex items-start gap-3 rounded-xl border p-3.5 shadow-lg transition-all ${VARIANT_STYLES[toast.variant]}`}
        >
          <div className="mt-0.5">
            <ToastIcon variant={toast.variant} />
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium">{toast.title}</p>
            {toast.message && (
              <p className="mt-0.5 text-xs opacity-80">{toast.message}</p>
            )}
          </div>
          <button
            type="button"
            onClick={() => removeToast(toast.id)}
            aria-label="Dismiss notification"
            className="rounded p-0.5 opacity-60 hover:bg-black/5 hover:opacity-100"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      ))}
    </div>
  );
}
