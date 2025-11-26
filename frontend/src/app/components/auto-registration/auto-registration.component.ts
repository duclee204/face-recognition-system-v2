import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { Subscription } from 'rxjs';

import { ApiService } from '../../services/api.service';
import { AutoRegistrationWebSocketService } from '../../services/auto-registration-websocket.service';
import { 
  AutoRegistrationStart, 
  AutoRegistrationGuidance,
  AutoRegistrationProgress 
} from '../../models/recognition.model';

@Component({
  selector: 'app-auto-registration',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './auto-registration.component.html',
  styleUrls: ['./auto-registration.component.scss']
})
export class AutoRegistrationComponent implements OnInit, OnDestroy {
  // Form data
  employeeData: AutoRegistrationStart = {
    employee_code: '',
    full_name: '',
    email: '',
    phone_number: '',
    position: ''
  };

  // State
  sessionStarted = false;
  sessionId = '';
  isCapturing = false;
  isCompleting = false;

  // Progress
  progress: AutoRegistrationProgress | null = null;
  currentGuidance: AutoRegistrationGuidance | null = null;

  // Visual feedback
  poseOk = false;
  framePreview = '';
  stableFramesProgress = 0;

  // WebSocket
  private wsSubscription?: Subscription;

  // Pose requirements
  readonly REQUIRED_POSES = ['center', 'left', 'right', 'up', 'down'];
  readonly POSE_INSTRUCTIONS = {
    center: 'Look straight at the camera',
    left: 'Turn your head to the LEFT',
    right: 'Turn your head to the RIGHT',
    up: 'Tilt your head UP',
    down: 'Tilt your head DOWN'
  };

  constructor(
    private apiService: ApiService,
    private wsService: AutoRegistrationWebSocketService,
    private router: Router
  ) {}

  ngOnInit(): void {
    // Check if there's an active session
    this.checkActiveSession();
  }

  ngOnDestroy(): void {
    this.disconnectWebSocket();
  }

  /**
   * Check for active session
   */
  checkActiveSession(): void {
    this.apiService.getActiveRegistrationSessions().subscribe({
      next: (response) => {
        if (response.count > 0) {
          console.log('Active sessions found:', response.active_sessions);
        }
      },
      error: (error) => {
        console.error('Error checking active sessions:', error);
      }
    });
  }

  /**
   * Start registration session
   */
  startSession(): void {
    if (!this.employeeData.employee_code || !this.employeeData.full_name) {
      alert('Please enter employee code and full name');
      return;
    }

    this.apiService.startAutoRegistration(this.employeeData).subscribe({
      next: (response) => {
        console.log('Session started:', response);
        this.sessionStarted = true;
        this.sessionId = response.session_id;
        this.progress = response.progress;

        // Connect WebSocket
        this.connectWebSocket();
      },
      error: (error) => {
        console.error('Error starting session:', error);
        alert('Failed to start registration session: ' + (error.error?.detail || error.message));
      }
    });
  }

  /**
   * Connect to WebSocket for auto capture
   */
  connectWebSocket(): void {
    this.isCapturing = true;

    this.wsSubscription = this.wsService
      .connect(this.employeeData.employee_code)
      .subscribe({
        next: (data) => {
          this.handleWebSocketMessage(data);
        },
        error: (error) => {
          console.error('WebSocket error:', error);
          this.isCapturing = false;
          alert('WebSocket connection error');
        },
        complete: () => {
          console.log('WebSocket closed');
          this.isCapturing = false;
        }
      });
  }

  /**
   * Handle WebSocket messages
   */
  handleWebSocketMessage(data: AutoRegistrationGuidance): void {
    this.currentGuidance = data;

    switch (data.type) {
      case 'guidance':
        this.handleGuidanceMessage(data);
        break;

      case 'complete':
        this.handleCompleteMessage(data);
        break;

      case 'frame':
        this.handleFrameMessage(data);
        break;

      case 'info':
        console.log('Info:', data.message);
        break;

      case 'error':
        console.error('Error:', data.message);
        alert('Error: ' + data.message);
        break;
    }
  }

  /**
   * Handle guidance message
   */
  handleGuidanceMessage(data: AutoRegistrationGuidance): void {
    this.currentGuidance = data;  // Update current guidance with all data including yaw, pitch, roll
    this.poseOk = data.pose_ok || false;

    // Update progress bar for holding
    if (data.status === 'holding' && data.stable_frames && data.hold_frames_required) {
      this.stableFramesProgress = (data.stable_frames / data.hold_frames_required) * 100;
    } else {
      this.stableFramesProgress = 0;
    }

    // Update progress if available
    if (data.progress) {
      this.progress = data.progress;
    }

    // Play sound on capture
    if (data.status === 'captured') {
      this.playSuccessSound();
    }
  }

  /**
   * Handle complete message
   */
  handleCompleteMessage(data: AutoRegistrationGuidance): void {
    console.log('All poses captured!', data);
    this.progress = data.progress || null;

    // Disconnect WebSocket
    this.disconnectWebSocket();

    // Show completion UI
    setTimeout(() => {
      if (confirm('All poses captured! Do you want to complete registration?')) {
        this.completeRegistration();
      }
    }, 500);
  }

  /**
   * Handle frame preview message
   */
  handleFrameMessage(data: AutoRegistrationGuidance): void {
    if (data.image) {
      this.framePreview = 'data:image/jpeg;base64,' + data.image;
    }
  }

  /**
   * Complete registration
   */
  completeRegistration(): void {
    if (!this.sessionId) {
      alert('No active session');
      return;
    }

    this.isCompleting = true;

    this.apiService.completeAutoRegistration({
      employee_code: this.employeeData.employee_code,
      session_id: this.sessionId
    }).subscribe({
      next: (response) => {
        console.log('Registration completed:', response);
        alert(`✅ Registration successful!\n\nEmployee ID: ${response.employee_id}\nTotal images: ${response.total_images}\nEmbeddings: ${response.embeddings_count}\n\nYou will be redirected to recognition page.`);
        
        // Navigate to recognition page
        this.router.navigate(['/recognition']);
      },
      error: (error) => {
        console.error('Error completing registration:', error);
        alert('Failed to complete registration: ' + (error.error?.detail || error.message));
        this.isCompleting = false;
      }
    });
  }

  /**
   * Cancel registration
   */
  cancelRegistration(): void {
    if (!confirm('Are you sure you want to cancel registration?')) {
      return;
    }

    this.disconnectWebSocket();

    if (this.sessionId) {
      this.apiService.cancelAutoRegistration(this.employeeData.employee_code).subscribe({
        next: () => {
          console.log('Registration cancelled');
          this.resetForm();
        },
        error: (error) => {
          console.error('Error cancelling registration:', error);
        }
      });
    } else {
      this.resetForm();
    }
  }

  /**
   * Disconnect WebSocket
   */
  disconnectWebSocket(): void {
    if (this.wsSubscription) {
      this.wsSubscription.unsubscribe();
      this.wsSubscription = undefined;
    }
    this.wsService.disconnect();
    this.isCapturing = false;
  }

  /**
   * Reset form
   */
  resetForm(): void {
    this.sessionStarted = false;
    this.sessionId = '';
    this.isCapturing = false;
    this.isCompleting = false;
    this.progress = null;
    this.currentGuidance = null;
    this.poseOk = false;
    this.framePreview = '';
    this.stableFramesProgress = 0;
    
    this.employeeData = {
      employee_code: '',
      full_name: '',
      email: '',
      phone_number: '',
      position: ''
    };
  }

  /**
   * Play success sound
   */
  playSuccessSound(): void {
    try {
      const audio = new Audio('assets/sounds/capture.mp3');
      audio.play().catch(e => console.log('Could not play sound:', e));
    } catch (e) {
      console.log('Sound not available');
    }
  }

  /**
   * Get border color based on pose status
   */
  getBorderColor(): string {
    if (!this.isCapturing || !this.currentGuidance) {
      return '#ccc';
    }

    if (this.currentGuidance.status === 'no_face' || this.currentGuidance.status === 'multiple_faces') {
      return '#ff9800';  // Orange
    }

    return this.poseOk ? '#4caf50' : '#f44336';  // Green : Red
  }

  /**
   * Get current pose instruction
   */
  getCurrentPoseInstruction(): string {
    if (!this.progress) {
      return 'Initializing...';
    }

    const pose = this.progress.current_target_pose as keyof typeof this.POSE_INSTRUCTIONS;
    return this.POSE_INSTRUCTIONS[pose] || 'Follow the guidance';
  }
}
