export interface AttendanceLog {
  id: number;
  employee_id: number;
  work_date?: string;
  check_in?: string;
  check_out?: string;
  total_hours?: number;
  status?: string;  // 'checked-in' | 'completed' | 'pending'
  confidence_score?: number;
  recognition_method?: string;
  snapshot_path?: string;
  camera_id?: number;
  notes?: string;
}

export interface AttendanceStats {
  total_today: number;
  total_this_week: number;
  total_this_month: number;
  unique_employees_today: number;
}

export interface CheckInStatus {
  success: boolean;
  employee_id: number;
  status: string;  // 'not-checked-in' | 'checked-in'
  has_checked_in_today: boolean;
  date: string;
  message: string;
  check_in?: string;
  check_out?: string;
  total_hours?: number;
}
