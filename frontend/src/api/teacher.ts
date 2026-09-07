import { apiFetch } from "./client";
import type { ApiGoogleStatus } from "./types";

export function googleStatus() {
  return apiFetch<ApiGoogleStatus>("/api/google/status/");
}

export function disconnectGoogle() {
  return apiFetch<void>("/api/google/disconnect/", { method: "POST" });
}
