export interface Employee {
  id: number;
  employee_code: string;
  full_name: string;
  email?: string;
  phone_number?: string;
  position?: string;
  base_salary?: number;
  standard_work_days?: number;
  department_id?: number;
  total_embeddings: number;
  status?: string;  // 'active' | 'inactive'
  created_at: string;
  updated_at?: string;
}

export interface EmployeeCreate {
  employee_code: string;
  full_name: string;
  email?: string;
  phone_number?: string;
  position?: string;
  base_salary?: number;
  standard_work_days?: number;
  department_id?: number;
}

export interface EmployeeUpdate {
  full_name?: string;
  email?: string;
  phone_number?: string;
  position?: string;
  base_salary?: number;
  standard_work_days?: number;
  department_id?: number;
  status?: string;
}
