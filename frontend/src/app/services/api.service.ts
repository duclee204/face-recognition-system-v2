import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Employee, EmployeeCreate, EmployeeUpdate } from '../models/employee.model';
import { AttendanceLog, AttendanceStats, CheckInStatus } from '../models/attendance.model';
import { 
  RegistrationSession, 
  RegistrationFrame, 
  RegistrationComplete,
  AutoRegistrationStart,
  AutoRegistrationProgress,
  AutoRegistrationComplete,
  AutoRegistrationCompleteResponse
} from '../models/recognition.model';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private baseUrl = 'http://localhost:8000/api/v1';

  constructor(private http: HttpClient) { }

  // ==================== EMPLOYEE APIs ====================
  
  /**
   * Start registration session
   */
  startRegistration(employee: EmployeeCreate): Observable<RegistrationSession> {
    return this.http.post<RegistrationSession>(
      `${this.baseUrl}/employees/register/start`,
      employee
    );
  }

  /**
   * Upload registration frame
   */
  uploadFrame(sessionId: string, frame: RegistrationFrame): Observable<any> {
    return this.http.post(
      `${this.baseUrl}/employees/register/frame/${sessionId}`,
      frame
    );
  }

  /**
   * Complete registration
   */
  completeRegistration(sessionId: string): Observable<RegistrationComplete> {
    return this.http.post<RegistrationComplete>(
      `${this.baseUrl}/employees/register/complete`,
      { session_id: sessionId }
    );
  }

  /**
   * Get all employees
   */
  getEmployees(skip = 0, limit = 100, status?: string): Observable<{ total: number; employees: Employee[] }> {
    let params = new HttpParams()
      .set('skip', skip.toString())
      .set('limit', limit.toString());
    
    if (status !== undefined) {
      params = params.set('status', status);
    }

    return this.http.get<{ total: number; employees: Employee[] }>(
      `${this.baseUrl}/employees`,
      { params }
    );
  }

  /**
   * Get employee by ID
   */
  getEmployee(id: number): Observable<Employee> {
    return this.http.get<Employee>(`${this.baseUrl}/employees/${id}`);
  }

  /**
   * Update employee
   */
  updateEmployee(id: number, data: EmployeeUpdate): Observable<Employee> {
    return this.http.put<Employee>(`${this.baseUrl}/employees/${id}`, data);
  }

  /**
   * Delete employee (soft delete)
   */
  deleteEmployee(id: number): Observable<any> {
    return this.http.delete(`${this.baseUrl}/employees/${id}`);
  }

  // ==================== RECOGNITION APIs ====================

  /**
   * Get camera info
   */
  getCameraInfo(): Observable<any> {
    return this.http.get(`${this.baseUrl}/recognition/camera/info`);
  }

  /**
   * Get list of available cameras
   */
  listCameras(): Observable<{ success: boolean; cameras: any[]; count: number }> {
    return this.http.get<{ success: boolean; cameras: any[]; count: number }>(
      `${this.baseUrl}/recognition/camera/list`
    );
  }

  /**
   * Get recognized employees
   */
  getRecognizedEmployees(): Observable<{ success: boolean; recognized: any[]; count: number }> {
    return this.http.get<{ success: boolean; recognized: any[]; count: number }>(
      `${this.baseUrl}/recognition/recognized`
    );
  }

  // ==================== ATTENDANCE APIs ====================

  /**
   * Get attendance logs
   */
  getAttendanceLogs(
    skip = 0,
    limit = 50,
    employeeId?: number,
    startDate?: string,
    endDate?: string
  ): Observable<{ total: number; logs: AttendanceLog[] }> {
    let params = new HttpParams()
      .set('skip', skip.toString())
      .set('limit', limit.toString());

    if (employeeId) {
      params = params.set('employee_id', employeeId.toString());
    }
    if (startDate) {
      params = params.set('start_date', startDate);
    }
    if (endDate) {
      params = params.set('end_date', endDate);
    }

    return this.http.get<{ total: number; logs: AttendanceLog[] }>(
      `${this.baseUrl}/attendance/logs`,
      { params }
    );
  }

  /**
   * Get today's attendance
   */
  getTodayAttendance(): Observable<{ success: boolean; date: string; total: number; logs: AttendanceLog[] }> {
    return this.http.get<any>(`${this.baseUrl}/attendance/today`);
  }

  /**
   * Get attendance statistics
   */
  getAttendanceStats(): Observable<AttendanceStats> {
    return this.http.get<AttendanceStats>(`${this.baseUrl}/attendance/stats`);
  }

  /**
   * Check employee check-in status
   */
  getCheckInStatus(employeeId: number): Observable<CheckInStatus> {
    return this.http.get<CheckInStatus>(`${this.baseUrl}/attendance/check-in-status/${employeeId}`);
  }

  // ==================== AUTO REGISTRATION APIs ====================

  /**
   * Start auto registration session
   */
  startAutoRegistration(data: AutoRegistrationStart): Observable<any> {
    return this.http.post(`${this.baseUrl}/auto-registration/start`, data);
  }

  /**
   * Get auto registration progress
   */
  getAutoRegistrationProgress(employeeCode: string): Observable<AutoRegistrationProgress> {
    return this.http.get<AutoRegistrationProgress>(
      `${this.baseUrl}/auto-registration/progress/${employeeCode}`
    );
  }

  /**
   * Complete auto registration
   */
  completeAutoRegistration(data: AutoRegistrationComplete): Observable<AutoRegistrationCompleteResponse> {
    return this.http.post<AutoRegistrationCompleteResponse>(
      `${this.baseUrl}/auto-registration/complete`,
      data
    );
  }

  /**
   * Cancel auto registration session
   */
  cancelAutoRegistration(employeeCode: string): Observable<any> {
    return this.http.delete(`${this.baseUrl}/auto-registration/cancel/${employeeCode}`);
  }

  /**
   * Get active registration sessions
   */
  getActiveRegistrationSessions(): Observable<{ success: boolean; active_sessions: string[]; count: number }> {
    return this.http.get<any>(`${this.baseUrl}/auto-registration/active-sessions`);
  }

  // ==================== SYSTEM APIs ====================

  /**
   * Get system status
   */
  getSystemStatus(): Observable<any> {
    return this.http.get(`${this.baseUrl}/system/status`);
  }

  /**
   * Train SVM model
   */
  trainModel(forceRetrain = false): Observable<any> {
    return this.http.post(`${this.baseUrl}/system/train-model`, {
      force_retrain: forceRetrain
    });
  }

  /**
   * Reload models
   */
  reloadModels(): Observable<any> {
    return this.http.post(`${this.baseUrl}/system/reload-models`, {});
  }

  /**
   * Health check
   */
  healthCheck(): Observable<any> {
    return this.http.get(`${this.baseUrl}/system/health`);
  }
}
