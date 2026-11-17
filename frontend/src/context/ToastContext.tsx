import {
  createContext,
  useCallback,
  useContext,
  useState,
  type ReactNode,
} from "react";

export type ToastVariant = "info" | "success" | "warning" | "error";

export interface ToastItem {
  id: string;
  title: string;
  message?: string;
  variant: ToastVariant;
}

interface ToastContextValue {
  toasts: ToastItem[];
  addToast: (
    title: string,
    options?: { message?: string; variant?: ToastVariant; durationMs?: number }
  ) => void;
  removeToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const addToast = useCallback(
    (
      title: string,
      options?: { message?: string; variant?: ToastVariant; durationMs?: number }
    ) => {
      const id = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
      const variant = options?.variant ?? "info";
      const durationMs = options?.durationMs ?? 4500;

      setToasts((prev) => [
        ...prev.slice(-4),
        { id, title, message: options?.message, variant },
      ]);

      window.setTimeout(() => {
        removeToast(id);
      }, durationMs);
    },
    [removeToast]
  );

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast }}>
      {children}
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return ctx;
}
