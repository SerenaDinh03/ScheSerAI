export type StudentStatus = "active" | "inactive";

export interface Student {
  id: string;
  name: string;
  dob: string | null;
  startDate: string;
  pricePerSession: number;
  status: StudentStatus;
  note: string;
}

export type SessionStatus = "scheduled" | "rescheduled";
export type AttendanceStatus = "present" | "absent" | null;

export interface Session {
  id: string;
  studentId: string;
  studentName: string;
  date: string;
  startTime: string;
  endTime: string;
  status: SessionStatus;
  attendance: AttendanceStatus;
  googleSynced: boolean;
}

export interface MonthlyReport {
  id: string;
  studentId: string;
  studentName: string;
  month: number;
  year: number;
  totalSessions: number;
  totalAmount: number;
  generatedAt: string;
  format: "pdf" | "png";
}

export interface AppNotification {
  id: string;
  message: string;
  isRead: boolean;
  createdAt: string;
}

export interface TeacherProfile {
  name: string;
  email: string;
  googleConnected: boolean;
  googleAccountEmail: string;
  lastSyncAt: string | null;
}
