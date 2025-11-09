import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { AttendanceStats } from '../../models/attendance.model';

@Component({
  selector: 'app-dashboard',
  imports: [CommonModule],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss'
})
export class DashboardComponent implements OnInit {
  stats: AttendanceStats | null = null;
  systemStatus: any = null;
  totalEmployees: number = 0;
  loading = true;
  error: string | null = null;

  constructor(private apiService: ApiService) {}

  ngOnInit() {
    this.loadDashboardData();
  }

  loadDashboardData() {
    this.loading = true;
    this.error = null;

    // Load attendance stats
    this.apiService.getAttendanceStats().subscribe({
      next: (stats) => {
        this.stats = stats;
      },
      error: (err) => {
        console.error('Failed to load stats:', err);
        this.error = 'Failed to load attendance statistics';
      }
    });

    // Load system status
    this.apiService.getSystemStatus().subscribe({
      next: (status) => {
        this.systemStatus = status;
        this.totalEmployees = status.total_employees || 0;
        this.loading = false;
      },
      error: (err) => {
        console.error('Failed to load system status:', err);
        this.loading = false;
      }
    });
  }

  refresh() {
    this.loadDashboardData();
  }
}
