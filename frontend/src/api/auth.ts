import { apiRequest, clearTokens, setTokens } from "./client";
import type { HealthResponse, Token, UserRead } from "../types/api";

export async function registerUser(payload: {
  username: string;
  email: string;
  password: string;
}): Promise<UserRead> {
  return apiRequest<UserRead>("/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
    skipAuth: true,
  });
}

export async function loginUser(
  username: string,
  password: string
): Promise<Token> {
  const form = new URLSearchParams();
  form.set("username", username);
  form.set("password", password);

  const token = await apiRequest<Token>("/auth/login", {
    method: "POST",
    body: form,
    skipAuth: true,
  });
  setTokens(token.access_token, token.refresh_token);
  return token;
}

export async function fetchCurrentUser(): Promise<UserRead> {
  return apiRequest<UserRead>("/auth/me", { method: "GET" });
}

export function logoutUser(): void {
  clearTokens();
}

export async function fetchHealth(): Promise<HealthResponse> {
  return apiRequest<HealthResponse>("/health", {
    method: "GET",
    skipAuth: true,
  });
}
