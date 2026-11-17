import { apiRequest, downloadProtectedFile } from "./client";
import type { AttachmentRead } from "../types/api";

export const ALLOWED_EXTENSIONS = [
  ".txt",
  ".md",
  ".pdf",
  ".png",
  ".jpg",
  ".jpeg",
  ".gif",
  ".csv",
  ".json",
  ".zip",
];

export const MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024; // 10 MB

export function validateAttachmentFile(file: File): string | null {
  if (file.size === 0) {
    return "File cannot be empty.";
  }
  if (file.size > MAX_UPLOAD_SIZE_BYTES) {
    return "File exceeds the 10 MB maximum size limit.";
  }
  const dotIdx = file.name.lastIndexOf(".");
  const ext = dotIdx >= 0 ? file.name.slice(dotIdx).toLowerCase() : "";
  if (!ALLOWED_EXTENSIONS.includes(ext)) {
    return `File type '${ext || "unknown"}' is not allowed. Allowed: ${ALLOWED_EXTENSIONS.join(", ")}`;
  }
  return null;
}

export async function uploadAttachment(
  taskId: number,
  file: File
): Promise<AttachmentRead> {
  const formData = new FormData();
  formData.append("file", file);

  return apiRequest<AttachmentRead>(`/tasks/${taskId}/attachments`, {
    method: "POST",
    body: formData,
  });
}

export async function listTaskAttachments(
  taskId: number
): Promise<AttachmentRead[]> {
  return apiRequest<AttachmentRead[]>(`/tasks/${taskId}/attachments`, {
    method: "GET",
  });
}

export async function downloadAttachment(
  attachmentId: number,
  filename: string
): Promise<void> {
  await downloadProtectedFile(
    `/attachments/${attachmentId}/download`,
    filename
  );
}

export async function deleteAttachment(attachmentId: number): Promise<void> {
  return apiRequest<void>(`/attachments/${attachmentId}`, {
    method: "DELETE",
  });
}
