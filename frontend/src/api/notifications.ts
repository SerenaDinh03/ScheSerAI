import { apiFetch } from "./client";
import type { ApiNotification } from "./types";

export function listNotifications() {
  return apiFetch<ApiNotification[]>("/api/notifications/");
}

export function unreadCount() {
  return apiFetch<{ count: number }>("/api/notifications/unread-count/");
}

export function markNotificationRead(id: string) {
  return apiFetch<ApiNotification>(`/api/notifications/${id}/mark-read/`, { method: "POST" });
}

export function markAllNotificationsRead() {
  return apiFetch<{ updated: number }>("/api/notifications/mark-all-read/", { method: "POST" });
}
