import { apiFetch } from "./client";
import type { ApiBillingPreview, ApiMonthlyReport } from "./types";

export function listMonthlyReports(params: { student?: string } = {}) {
  return apiFetch<ApiMonthlyReport[]>("/api/monthly-reports/", { params });
}

export function previewReport(studentId: string, month: number, year: number) {
  return apiFetch<ApiBillingPreview>("/api/monthly-reports/preview/", {
    params: { student: studentId, month, year },
  });
}

export function generateReport(
  studentId: string,
  month: number,
  year: number,
  format: "pdf" | "png",
) {
  return apiFetch<ApiMonthlyReport>("/api/monthly-reports/generate/", {
    method: "POST",
    body: { student: studentId, month, year, format },
  });
}
