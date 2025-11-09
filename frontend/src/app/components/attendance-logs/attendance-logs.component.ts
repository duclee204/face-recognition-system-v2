import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { AttendanceLog } from '../../models/attendance.model';

@Component({
  selector: 'app-attendance-logs',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './attendance-logs.component.html',
  styleUrl: './attendance-logs.component.scss'
})
export class AttendanceLogsComponent implements OnInit {
  logs: AttendanceLog[] = [];
  filteredLogs: AttendanceLog[] = [];
  todayLogs: AttendanceLog[] = [];
  loading = false;
  error = '';
  
  // Expose Math for template
  Math = Math;
  
  // Pagination
  currentPage = 1;
  pageSize = 20;
  totalLogs = 0;
  totalPages = 0;
  
  // Filters
  searchText = '';
  filterStartDate = '';
  filterEndDate = '';
  selectedEmployeeId: number | undefined = undefined;
  
  // View mode
  viewMode: 'all' | 'today' = 'today';
  
  // Stats
  todayTotal = 0;

  constructor(private apiService: ApiService) {}

  ngOnInit() {
    this.loadTodayAttendance();
    this.setDefaultDates();
  }

  /**
   * Set default date range (last 7 days)
   */
  setDefaultDates() {
    const today = new Date();
    const weekAgo = new Date(today);
    weekAgo.setDate(weekAgo.getDate() - 7);
    
    this.filterEndDate = today.toISOString().split('T')[0];
    this.filterStartDate = weekAgo.toISOString().split('T')[0];
  }

  /**
   * Load today's attendance
   */
  loadTodayAttendance() {
    this.loading = true;
    this.error = '';
    
    this.apiService.getTodayAttendance().subscribe({
      next: (response) => {
        this.todayLogs = response.logs;
        this.todayTotal = response.total;
        this.filteredLogs = this.todayLogs;
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Failed to load today\'s attendance: ' + (err.error?.detail || err.message);
        this.loading = false;
      }
    });
  }

  /**
   * Load all attendance logs with filters
   */
  loadAttendanceLogs() {
    this.loading = true;
    this.error = '';
    
    const skip = (this.currentPage - 1) * this.pageSize;
    
    this.apiService.getAttendanceLogs(
      skip,
      this.pageSize,
      this.selectedEmployeeId,
      this.filterStartDate,
      this.filterEndDate
    ).subscribe({
      next: (response) => {
        this.logs = response.logs;
        this.totalLogs = response.total;
        this.totalPages = Math.ceil(this.totalLogs / this.pageSize);
        this.applySearchFilter();
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Failed to load attendance logs: ' + (err.error?.detail || err.message);
        this.loading = false;
      }
    });
  }

  /**
   * Switch view mode
   */
  switchView(mode: 'all' | 'today') {
    this.viewMode = mode;
    
    if (mode === 'today') {
      this.loadTodayAttendance();
    } else {
      this.currentPage = 1;
      this.loadAttendanceLogs();
    }
  }

  /**
   * Apply search filter
   */
  applySearchFilter() {
    const dataSource = this.viewMode === 'today' ? this.todayLogs : this.logs;
    
    if (!this.searchText) {
      this.filteredLogs = dataSource;
      return;
    }
    
    const search = this.searchText.toLowerCase();
    this.filteredLogs = dataSource.filter(log => 
      log.employee_name.toLowerCase().includes(search) ||
      log.employee_code.toLowerCase().includes(search)
    );
  }

  /**
   * Search input change handler
   */
  onSearchChange() {
    this.applySearchFilter();
  }

  /**
   * Apply date filter
   */
  onFilterApply() {
    this.currentPage = 1;
    this.loadAttendanceLogs();
  }

  /**
   * Reset filters
   */
  resetFilters() {
    this.searchText = '';
    this.selectedEmployeeId = undefined;
    this.setDefaultDates();
    this.currentPage = 1;
    this.loadAttendanceLogs();
  }

  /**
   * Go to page
   */
  goToPage(page: number) {
    if (page < 1 || page > this.totalPages) return;
    this.currentPage = page;
    this.loadAttendanceLogs();
  }

  /**
   * Get page numbers for pagination
   */
  getPageNumbers(): number[] {
    const pages: number[] = [];
    const maxVisible = 5;
    
    let start = Math.max(1, this.currentPage - Math.floor(maxVisible / 2));
    let end = Math.min(this.totalPages, start + maxVisible - 1);
    
    if (end - start < maxVisible - 1) {
      start = Math.max(1, end - maxVisible + 1);
    }
    
    for (let i = start; i <= end; i++) {
      pages.push(i);
    }
    
    return pages;
  }

  /**
   * Format date
   */
  formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('vi-VN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    });
  }

  /**
   * Format time
   */
  formatTime(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleTimeString('vi-VN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  }

  /**
   * Format datetime
   */
  formatDateTime(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('vi-VN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  /**
   * Get method badge class
   */
  getMethodClass(method: string): string {
    return method === 'svm' ? 'method-svm' : 'method-cosine';
  }

  /**
   * Get confidence level class
   */
  getConfidenceClass(confidence: number): string {
    if (confidence >= 0.9) return 'confidence-high';
    if (confidence >= 0.7) return 'confidence-medium';
    return 'confidence-low';
  }

  /**
   * Export to CSV
   */
  exportToCSV() {
    const data = this.filteredLogs;
    
    if (data.length === 0) {
      alert('No data to export');
      return;
    }
    
    // Create CSV content
    const headers = ['ID', 'Employee Code', 'Employee Name', 'Check-in Time', 'Confidence', 'Method'];
    const rows = data.map(log => [
      log.id,
      log.employee_code,
      log.employee_name,
      this.formatDateTime(log.check_in_time),
      (log.confidence_score * 100).toFixed(1) + '%',
      log.recognition_method.toUpperCase()
    ]);
    
    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.join(','))
    ].join('\n');
    
    // Download file
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', `attendance_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
}
