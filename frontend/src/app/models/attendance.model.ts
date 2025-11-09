export interface AttendanceLog {
  id: number;
  employee_id: number;
  employee_code: string;
  employee_name: string;
  confidence_score: number;
  recognition_method: string;
  snapshot_path?: string;
  location?: string;
  check_in_time: string;
}

export interface AttendanceStats {
  total_today: number;
  total_this_week: number;
  total_this_month: number;
  unique_employees_today: number;
}
