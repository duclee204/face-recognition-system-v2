import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { Employee, EmployeeUpdate } from '../../models/employee.model';

@Component({
  selector: 'app-employee-list',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './employee-list.component.html',
  styleUrl: './employee-list.component.scss'
})
export class EmployeeListComponent implements OnInit {
  employees: Employee[] = [];
  filteredEmployees: Employee[] = [];
  loading = false;
  error = '';
  
  // Pagination
  currentPage = 1;
  pageSize = 10;
  totalEmployees = 0;
  totalPages = 0;
  
  // Filters
  searchText = '';
  filterActive: boolean | undefined = undefined;
  
  // Edit modal
  showEditModal = false;
  editingEmployee: Employee | null = null;
  editForm: EmployeeUpdate = {
    full_name: '',
    department: '',
    position: '',
    is_active: true
  };
  
  // Delete confirmation
  showDeleteModal = false;
  deletingEmployee: Employee | null = null;

  constructor(
    private apiService: ApiService,
    private router: Router
  ) {}

  ngOnInit() {
    this.loadEmployees();
  }

  /**
   * Load employees from API
   */
  loadEmployees() {
    this.loading = true;
    this.error = '';
    
    const skip = (this.currentPage - 1) * this.pageSize;
    
    this.apiService.getEmployees(skip, this.pageSize, this.filterActive).subscribe({
      next: (response) => {
        this.employees = response.employees;
        this.totalEmployees = response.total;
        this.totalPages = Math.ceil(this.totalEmployees / this.pageSize);
        this.applyFilters();
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Failed to load employees: ' + (err.error?.detail || err.message);
        this.loading = false;
      }
    });
  }

  /**
   * Apply search filter
   */
  applyFilters() {
    if (!this.searchText) {
      this.filteredEmployees = this.employees;
      return;
    }
    
    const search = this.searchText.toLowerCase();
    this.filteredEmployees = this.employees.filter(emp => 
      emp.full_name.toLowerCase().includes(search) ||
      emp.employee_code.toLowerCase().includes(search) ||
      (emp.department && emp.department.toLowerCase().includes(search)) ||
      (emp.position && emp.position.toLowerCase().includes(search))
    );
  }

  /**
   * Search input change handler
   */
  onSearchChange() {
    this.applyFilters();
  }

  /**
   * Filter by active status
   */
  onFilterChange() {
    this.currentPage = 1;
    this.loadEmployees();
  }

  /**
   * Go to page
   */
  goToPage(page: number) {
    if (page < 1 || page > this.totalPages) return;
    this.currentPage = page;
    this.loadEmployees();
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
   * Open edit modal
   */
  openEditModal(employee: Employee) {
    this.editingEmployee = employee;
    this.editForm = {
      full_name: employee.full_name,
      department: employee.department || '',
      position: employee.position || '',
      is_active: employee.is_active
    };
    this.showEditModal = true;
  }

  /**
   * Close edit modal
   */
  closeEditModal() {
    this.showEditModal = false;
    this.editingEmployee = null;
  }

  /**
   * Save employee changes
   */
  saveEmployee() {
    if (!this.editingEmployee) return;
    
    this.loading = true;
    
    this.apiService.updateEmployee(this.editingEmployee.id, this.editForm).subscribe({
      next: (updated) => {
        // Update in list
        const index = this.employees.findIndex(e => e.id === updated.id);
        if (index !== -1) {
          this.employees[index] = updated;
        }
        this.applyFilters();
        this.closeEditModal();
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Failed to update employee: ' + (err.error?.detail || err.message);
        this.loading = false;
      }
    });
  }

  /**
   * Open delete confirmation
   */
  openDeleteModal(employee: Employee) {
    this.deletingEmployee = employee;
    this.showDeleteModal = true;
  }

  /**
   * Close delete modal
   */
  closeDeleteModal() {
    this.showDeleteModal = false;
    this.deletingEmployee = null;
  }

  /**
   * Confirm delete
   */
  confirmDelete() {
    if (!this.deletingEmployee) return;
    
    this.loading = true;
    
    this.apiService.deleteEmployee(this.deletingEmployee.id).subscribe({
      next: () => {
        this.closeDeleteModal();
        this.loadEmployees(); // Reload list
      },
      error: (err) => {
        this.error = 'Failed to delete employee: ' + (err.error?.detail || err.message);
        this.loading = false;
        this.closeDeleteModal();
      }
    });
  }

  /**
   * Navigate to registration page
   */
  goToRegistration() {
    this.router.navigate(['/register']);
  }

  /**
   * Get status badge class
   */
  getStatusClass(isActive: boolean): string {
    return isActive ? 'status-active' : 'status-inactive';
  }

  /**
   * Format date
   */
  formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('vi-VN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  }
}
