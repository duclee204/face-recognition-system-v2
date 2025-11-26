import { Component, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { EmployeeCreate } from '../../models/employee.model';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-registration',
  imports: [CommonModule, FormsModule],
  templateUrl: './registration.component.html',
  styleUrl: './registration.component.scss'
})
export class RegistrationComponent implements OnInit, OnDestroy {
  @ViewChild('videoElement') videoElement!: ElementRef<HTMLVideoElement>;
  @ViewChild('canvasElement') canvasElement!: ElementRef<HTMLCanvasElement>;
  @ViewChild('fileInput') fileInput!: ElementRef<HTMLInputElement>;

  // Form data
  employee: EmployeeCreate = {
    employee_code: '',
    full_name: '',
    email: '',
    phone_number: '',
    department_id: undefined,
    position: ''
  };

  // Registration mode
  registrationMode: 'upload' | 'camera' = 'upload';
  
  // Upload mode
  selectedFiles: File[] = [];
  previewUrls: string[] = [];
  
  // Registration state
  step: 'form' | 'scanning' | 'processing' | 'complete' | 'error' = 'form';
  sessionId: string = '';
  
  // Camera & Scanning
  stream: MediaStream | null = null;
  framesCollected: number = 0;
  targetFrames: number = 100;
  scanningProgress: number = 0;
  isScanning: boolean = false;
  
  // Messages
  message: string = '';
  errorMessage: string = '';
  
  // Timers
  private scanInterval: any;
  private frameInterval: any;

  constructor(
    private apiService: ApiService,
    private http: HttpClient,
    public router: Router
  ) {}

  ngOnInit() {}

  ngOnDestroy() {
    this.stopCamera();
    this.clearPreviews();
  }

  /**
   * Handle file selection
   */
  onFileSelect(event: Event) {
    const input = event.target as HTMLInputElement;
    if (!input.files) return;

    const files = Array.from(input.files);
    
    // Validate number of files
    if (files.length < 5) {
      this.errorMessage = 'Please select at least 5 images';
      return;
    }
    
    if (files.length > 30) {
      this.errorMessage = 'Maximum 30 images allowed';
      return;
    }

    // Validate file types
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png'];
    const invalidFiles = files.filter(f => !validTypes.includes(f.type));
    
    if (invalidFiles.length > 0) {
      this.errorMessage = 'Only JPEG and PNG images are allowed';
      return;
    }

    this.selectedFiles = files;
    this.errorMessage = '';
    
    // Create previews
    this.clearPreviews();
    files.slice(0, 10).forEach(file => {
      const reader = new FileReader();
      reader.onload = (e: any) => {
        this.previewUrls.push(e.target.result);
      };
      reader.readAsDataURL(file);
    });
  }

  /**
   * Clear preview URLs
   */
  clearPreviews() {
    this.previewUrls.forEach(url => URL.revokeObjectURL(url));
    this.previewUrls = [];
  }

  /**
   * Remove selected files
   */
  removeFiles() {
    this.selectedFiles = [];
    this.clearPreviews();
    if (this.fileInput) {
      this.fileInput.nativeElement.value = '';
    }
  }

  /**
   * Submit registration with uploaded images
   */
  submitWithImages() {
    // Validate form
    if (!this.employee.employee_code || !this.employee.full_name) {
      this.errorMessage = 'Please fill in Employee Code and Full Name';
      return;
    }

    if (this.selectedFiles.length < 5) {
      this.errorMessage = 'Please select at least 5 images';
      return;
    }

    this.step = 'processing';
    this.message = 'Uploading images and extracting face embeddings...';

    // Create FormData
    const formData = new FormData();
    formData.append('employee_code', this.employee.employee_code);
    formData.append('name', this.employee.full_name);
    
    if (this.employee.email) formData.append('email', this.employee.email);
    if (this.employee.phone_number) formData.append('phone_number', this.employee.phone_number);
    if (this.employee.department_id) formData.append('department_id', this.employee.department_id.toString());
    if (this.employee.position) formData.append('position', this.employee.position);
    
    // Append all images
    this.selectedFiles.forEach((file, index) => {
      formData.append('images', file, file.name);
    });

    // Upload to backend
    this.http.post<any>('http://localhost:8000/api/v1/employees/register/upload', formData)
      .subscribe({
        next: (response) => {
          this.step = 'complete';
          this.message = `✅ Successfully registered ${this.employee.full_name}! 
                         ${response.total_embeddings} embeddings created from ${this.selectedFiles.length} images.
                         Processing time: ${response.processing_time.toFixed(2)}s`;
          
          // Redirect after 3 seconds
          setTimeout(() => {
            this.router.navigate(['/employees']);
          }, 3000);
        },
        error: (error) => {
          console.error('Failed to register:', error);
          this.errorMessage = error.error?.detail || 'Failed to complete registration';
          this.step = 'error';
        }
      });
  }

  /**
   * Start registration process
   */
  startRegistration() {
    // Validate form
    if (!this.employee.employee_code || !this.employee.full_name) {
      this.errorMessage = 'Please fill in Employee Code and Full Name';
      return;
    }

    this.step = 'processing';
    this.message = 'Initializing registration...';

    // Call API to start session
    this.apiService.startRegistration(this.employee).subscribe({
      next: (response) => {
        this.sessionId = response.session_id;
        this.step = 'scanning';
        this.message = 'Please look at the camera and slowly move your head in a circle';
        this.startCamera();
      },
      error: (error) => {
        console.error('Failed to start registration:', error);
        this.errorMessage = error.error?.detail || 'Failed to start registration';
        this.step = 'error';
      }
    });
  }

  /**
   * Start camera
   */
  async startCamera() {
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, facingMode: 'user' }
      });

      setTimeout(() => {
        if (this.videoElement) {
          this.videoElement.nativeElement.srcObject = this.stream;
          this.videoElement.nativeElement.play();
          
          // Start scanning after video is ready
          setTimeout(() => this.startScanning(), 1000);
        }
      }, 100);
    } catch (error) {
      console.error('Camera access denied:', error);
      this.errorMessage = 'Cannot access camera. Please allow camera permissions.';
      this.step = 'error';
    }
  }

  /**
   * Stop camera
   */
  stopCamera() {
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
    }
    if (this.scanInterval) clearInterval(this.scanInterval);
    if (this.frameInterval) clearInterval(this.frameInterval);
  }

  /**
   * Start scanning - capture frames
   */
  startScanning() {
    this.isScanning = true;
    this.framesCollected = 0;
    this.scanningProgress = 0;

    // Capture frame every 100ms
    this.frameInterval = setInterval(() => {
      if (this.framesCollected >= this.targetFrames) {
        this.stopScanning();
        return;
      }

      this.captureFrame();
    }, 100); // 10 FPS

    // Update progress
    this.scanInterval = setInterval(() => {
      this.scanningProgress = (this.framesCollected / this.targetFrames) * 100;
    }, 100);
  }

  /**
   * Capture single frame and upload
   */
  captureFrame() {
    if (!this.videoElement || !this.canvasElement) return;

    const video = this.videoElement.nativeElement;
    const canvas = this.canvasElement.nativeElement;
    const ctx = canvas.getContext('2d');

    if (!ctx) return;

    // Set canvas size
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // Draw video frame to canvas
    ctx.drawImage(video, 0, 0);

    // Convert to base64
    const frameData = canvas.toDataURL('image/jpeg', 0.8);

    // Upload frame
    this.apiService.uploadFrame(this.sessionId, {
      frame_data: frameData,
      frame_number: this.framesCollected + 1,
      timestamp: Date.now() / 1000
    }).subscribe({
      next: () => {
        this.framesCollected++;
      },
      error: (error) => {
        console.error('Failed to upload frame:', error);
      }
    });
  }

  /**
   * Stop scanning
   */
  stopScanning() {
    this.isScanning = false;
    this.stopCamera();
    this.completeRegistration();
  }

  /**
   * Complete registration
   */
  completeRegistration() {
    this.step = 'processing';
    this.message = 'Processing frames and training model...';

    this.apiService.completeRegistration(this.sessionId).subscribe({
      next: (response) => {
        this.step = 'complete';
        this.message = `✅ Successfully registered ${this.employee.full_name}! 
                       ${response.total_embeddings} embeddings created.
                       Processing time: ${response.processing_time.toFixed(2)}s`;
        
        // Redirect after 3 seconds
        setTimeout(() => {
          this.router.navigate(['/employees']);
        }, 3000);
      },
      error: (error) => {
        console.error('Failed to complete registration:', error);
        this.errorMessage = error.error?.detail || 'Failed to complete registration';
        this.step = 'error';
      }
    });
  }

  /**
   * Reset and start over
   */
  reset() {
    this.stopCamera();
    this.step = 'form';
    this.sessionId = '';
    this.framesCollected = 0;
    this.scanningProgress = 0;
    this.message = '';
    this.errorMessage = '';
    this.employee = {
      employee_code: '',
      full_name: '',
      email: '',
      phone_number: '',
      department_id: undefined,
      position: ''
    };
  }

  /**
   * Cancel registration
   */
  cancel() {
    this.stopCamera();
    this.router.navigate(['/dashboard']);
  }
}
