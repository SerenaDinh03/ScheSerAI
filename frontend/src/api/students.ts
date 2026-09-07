import { apiFetch } from "./client";
import type {
  ApiStudentCreatePayload,
  ApiStudentDetail,
  ApiStudentListItem,
  ApiStudentUpdatePayload,
} from "./types";

export function listStudents(params: { status?: string; search?: string } = {}) {
  return apiFetch<ApiStudentListItem[]>("/api/students/", { params });
}

export function getStudent(id: string) {
  return apiFetch<ApiStudentDetail>(`/api/students/${id}/`);
}

export function createStudent(payload: ApiStudentCreatePayload) {
  return apiFetch<ApiStudentDetail>("/api/students/", { method: "POST", body: payload });
}

export function updateStudent(id: string, payload: ApiStudentUpdatePayload) {
  return apiFetch<ApiStudentDetail>(`/api/students/${id}/`, { method: "PATCH", body: payload });
}

export function deactivateStudent(id: string) {
  return apiFetch<{ status: string; deleted_sessions_count: number }>(
    `/api/students/${id}/deactivate/`,
    { method: "POST" },
  );
}
