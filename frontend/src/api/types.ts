// Hình dạng JSON thật trả về từ Django REST Framework (xem backend/apps/*/serializers.py).
// DecimalField qua ModelSerializer serialize thành string ("200000"); nhưng số
// trả về trực tiếp từ 1 dict thường (vd billing preview) lại là number.

export type ApiStudentStatus = "active" | "inactive";
export type ApiSessionStatus = "scheduled" | "rescheduled";
export type ApiAttendanceStatus = "present" | "absent";

export interface ApiStudentListItem {
  id: string;
  name: string;
  age: number | null;
  price_per_session: string;
  status: ApiStudentStatus;
}

export interface ApiScheduleNested {
  id: string;
  day_of_week: number;
  day_of_week_display: string;
  start_time: string;
  end_time: string;
  is_active: boolean;
}

export interface ApiAttendance {
  id: string;
  session: string;
  session_date: string;
  status: ApiAttendanceStatus;
  is_billable: boolean;
  marked_at: string;
}

export interface ApiStudentDetail {
  id: string;
  name: string;
  dob: string | null;
  age: number | null;
  start_date: string;
  price_per_session: string;
  status: ApiStudentStatus;
  note: string;
  created_at: string;
  schedules: ApiScheduleNested[];
  recent_attendance: ApiAttendance[];
  sessions_this_month_count: number;
}

export interface ApiStudentCreatePayload {
  name: string;
  dob?: string | null;
  start_date: string;
  price_per_session: number;
  note?: string;
}

export interface ApiStudentUpdatePayload {
  name?: string;
  dob?: string | null;
  start_date?: string;
  note?: string;
  confirm?: boolean;
}

export interface ApiConfirmationRequired {
  requires_confirmation: true;
  warning: string;
}

export interface ApiSchedule {
  id: string;
  student: string;
  student_name: string;
  day_of_week: number;
  day_of_week_display: string;
  start_time: string;
  end_time: string;
  is_active: boolean;
}

export interface ApiSession {
  id: string;
  student: string;
  student_name: string;
  session_date: string;
  start_time: string;
  end_time: string;
  status: ApiSessionStatus;
  google_event_id: string;
  attendance: ApiAttendance | null;
}

export interface ApiMonthlyReport {
  id: string;
  student: string;
  student_name: string;
  month: number;
  year: number;
  total_sessions: number;
  total_amount: string;
  generated_at: string;
  download_url: string;
}

export interface ApiBillingPreviewRow {
  session_date: string;
  start_time: string;
  status: string;
  billable: boolean;
}

export interface ApiBillingPreview {
  student_name: string;
  month: number;
  year: number;
  sessions: ApiBillingPreviewRow[];
  total_sessions: number;
  price_per_session: number;
  total_amount: number;
}

export interface ApiNotification {
  id: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

export interface ApiGoogleStatus {
  connected: boolean;
  email: string;
  last_sync_at: string | null;
  last_sync_error: string | null;
}
