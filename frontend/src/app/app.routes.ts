import { Routes } from '@angular/router';
import { DashboardComponent } from './components/dashboard/dashboard.component';
import { RegistrationComponent } from './components/registration/registration.component';
import { RecognitionComponent } from './components/recognition/recognition.component';
import { EmployeeListComponent } from './components/employee-list/employee-list.component';
import { AttendanceLogsComponent } from './components/attendance-logs/attendance-logs.component';

export const routes: Routes = [
  { path: '', redirectTo: '/dashboard', pathMatch: 'full' },
  { path: 'dashboard', component: DashboardComponent },
  { path: 'registration', component: RegistrationComponent },
  { path: 'recognition', component: RecognitionComponent },
  { path: 'employees', component: EmployeeListComponent },
  { path: 'attendance', component: AttendanceLogsComponent },
  { path: '**', redirectTo: '/dashboard' }
];
