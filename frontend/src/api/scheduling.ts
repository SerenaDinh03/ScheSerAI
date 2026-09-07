import { apiFetch } from "./client";
import type { ApiAttendance, ApiAttendanceStatus, ApiSchedule, ApiSession } from "./types";

export function listSessions(
  params: { student?: string; date_from?: string; date_to?: string; pending?: boolean } = {},
) {
  return apiFetch<ApiSession[]>("/api/sessions/", { params });
}

export function createSession(payload: {
  student: string;
  session_date: string;
  start_time: string;
  end_time: string;
}) {
  return apiFetch<ApiSession>("/api/sessions/", { method: "POST", body: payload });
}

export function listSchedules(params: { student?: string } = {}) {
  return apiFetch<ApiSchedule[]>("/api/schedules/", { params });
}

export function createSchedule(payload: {
  student: string;
  day_of_week: number;
  start_time: string;
  end_time: string;
}) {
  return apiFetch<ApiSchedule>("/api/schedules/", { method: "POST", body: payload });
}

export function pauseSchedule(id: string) {
  return apiFetch<ApiSchedule>(`/api/schedules/${id}/pause/`, { method: "POST" });
}

export function resumeSchedule(id: string) {
  return apiFetch<ApiSchedule>(`/api/schedules/${id}/resume/`, { method: "POST" });
}

export function markAttendance(sessionId: string, status: ApiAttendanceStatus) {
  return apiFetch<ApiAttendance & { warning?: string }>(
    `/api/sessions/${sessionId}/mark-attendance/`,
    { method: "POST", body: { status } },
  );
}

export function rescheduleSession(
  sessionId: string,
  payload: { session_date: string; start_time: string; end_time?: string },
) {
  return apiFetch<ApiSession>(`/api/sessions/${sessionId}/reschedule/`, {
    method: "POST",
    body: payload,
  });
}

export function cancelSession(sessionId: string) {
  return apiFetch<void>(`/api/sessions/${sessionId}/cancel/`, { method: "POST" });
}
