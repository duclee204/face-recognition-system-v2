export interface Employee {
  id: number;
  employee_code: string;
  full_name: string;
  email?: string;
  phone?: string;
  department?: string;
  position?: string;
  total_embeddings: number;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface EmployeeCreate {
  employee_code: string;
  full_name: string;
  email?: string;
  phone?: string;
  department?: string;
  position?: string;
}

export interface EmployeeUpdate {
  full_name?: string;
  email?: string;
  phone?: string;
  department?: string;
  position?: string;
  is_active?: boolean;
}
