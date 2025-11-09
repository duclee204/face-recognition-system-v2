import { Component, OnInit, OnDestroy, ViewChild, ElementRef, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { WebsocketService } from '../../services/websocket.service';
import { RecognitionFrame, RecognizedFace } from '../../models/recognition.model';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-recognition',
  imports: [CommonModule],
  templateUrl: './recognition.component.html',
  styleUrl: './recognition.component.scss'
})
export class RecognitionComponent implements OnInit, OnDestroy, AfterViewInit {
  @ViewChild('canvasElement') canvasElement!: ElementRef<HTMLCanvasElement>;

  isConnected = false;
  isStreaming = false;
  currentFaces: RecognizedFace[] = [];
  recognizedEmployees: Map<string, { face: RecognizedFace, lastSeen: number }> = new Map();
  fps = 0;
  lastFrameTime = 0;
  message = '';
  errorMessage = '';

  private wsSubscription?: Subscription;
  private fpsInterval: any;
  private cleanupInterval: any;
  
  private readonly FACE_TIMEOUT = 10000; // Keep faces for 10 seconds

  constructor(private wsService: WebsocketService) {}

  ngOnInit() {
    // Cleanup old faces periodically
    this.cleanupInterval = setInterval(() => {
      this.cleanupOldFaces();
    }, 1000);
  }

  ngAfterViewInit() {
    // Auto-start when component loads
    setTimeout(() => this.startRecognition(), 500);
  }

  ngOnDestroy() {
    this.stopRecognition();
    
    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval);
    }
  }
  
  /**
   * Cleanup faces that haven't been seen recently
   */
  cleanupOldFaces() {
    const now = Date.now();
    const keysToDelete: string[] = [];
    let hasChanges = false;
    
    this.recognizedEmployees.forEach((value, key) => {
      if (now - value.lastSeen > this.FACE_TIMEOUT) {
        keysToDelete.push(key);
        hasChanges = true;
      }
    });
    
    keysToDelete.forEach(key => this.recognizedEmployees.delete(key));
    
    // Only update currentFaces if there were changes
    if (hasChanges) {
      this.currentFaces = Array.from(this.recognizedEmployees.values()).map(v => v.face);
    }
  }
  
  /**
   * TrackBy function for *ngFor to prevent unnecessary re-renders
   */
  trackByEmployeeCode(index: number, face: RecognizedFace): string {
    return face.employee_code;
  }

  /**
   * Start WebSocket recognition
   */
  startRecognition() {
    this.message = 'Connecting to recognition service...';
    this.errorMessage = '';

    this.wsSubscription = this.wsService.connect().subscribe({
      next: (frame: RecognitionFrame) => {
        this.handleFrame(frame);
      },
      error: (error) => {
        console.error('WebSocket error:', error);
        this.errorMessage = 'Connection error. Please check if backend is running.';
        this.isConnected = false;
        this.isStreaming = false;
      }
    });

    // Calculate FPS
    this.fpsInterval = setInterval(() => {
      const now = Date.now();
      if (this.lastFrameTime > 0) {
        const delta = (now - this.lastFrameTime) / 1000;
        this.fps = Math.round(1 / delta);
      }
    }, 1000);

    this.isConnected = true;
    this.message = 'Connected! Waiting for video stream...';
  }

  /**
   * Stop recognition
   */
  stopRecognition() {
    this.wsService.disconnect();
    this.isConnected = false;
    this.isStreaming = false;
    this.currentFaces = [];
    
    if (this.wsSubscription) {
      this.wsSubscription.unsubscribe();
    }
    
    if (this.fpsInterval) {
      clearInterval(this.fpsInterval);
    }

    // Clear canvas
    if (this.canvasElement) {
      const ctx = this.canvasElement.nativeElement.getContext('2d');
      if (ctx) {
        ctx.clearRect(0, 0, this.canvasElement.nativeElement.width, this.canvasElement.nativeElement.height);
      }
    }
  }

  /**
   * Handle incoming frame from WebSocket
   */
  handleFrame(frame: RecognitionFrame) {
    if (frame.type === 'info') {
      this.message = frame.message || '';
      return;
    }

    if (frame.type === 'error') {
      this.errorMessage = frame.message || 'Unknown error';
      return;
    }

    if (frame.type === 'frame' && frame.frame) {
      this.isStreaming = true;
      this.message = '';
      this.lastFrameTime = Date.now();

      // Display frame
      this.displayFrame(frame.frame);

      // Draw bounding boxes IMMEDIATELY from current frame (real-time)
      if (frame.faces && frame.faces.length > 0) {
        this.drawFaces(frame.faces);  // ← Real-time bounding boxes
        
        // Update recognized faces list with timestamp (for display below, cached 10s)
        // BUT exclude Unknown faces from the list
        const now = Date.now();
        let hasNewFaces = false;
        
        frame.faces.forEach(face => {
          // Skip Unknown faces - only show identified employees in the list
          if (face.employee_code === 'Unknown') {
            return;
          }
          
          const existing = this.recognizedEmployees.get(face.employee_code);
          if (!existing || existing.face.confidence_score !== face.confidence_score) {
            hasNewFaces = true;
          }
          
          this.recognizedEmployees.set(face.employee_code, {
            face: face,
            lastSeen: now
          });
        });
        
        // Only update currentFaces if there are new faces
        if (hasNewFaces || this.currentFaces.length !== this.recognizedEmployees.size) {
          this.currentFaces = Array.from(this.recognizedEmployees.values()).map(v => v.face);
        }
      } else {
        // No faces detected in current frame - don't draw any boxes
        // (but keep currentFaces list unchanged - will expire after timeout)
      }
    }
  }

  /**
   * Display video frame on canvas
   */
  displayFrame(base64Image: string) {
    if (!this.canvasElement) return;

    const canvas = this.canvasElement.nativeElement;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const img = new Image();
    img.onload = () => {
      // Set canvas size to match image
      canvas.width = img.width;
      canvas.height = img.height;

      // Draw image
      ctx.drawImage(img, 0, 0);
    };
    img.src = 'data:image/jpeg;base64,' + base64Image;
  }

  /**
   * Draw bounding boxes and labels for recognized faces
   */
  drawFaces(faces: RecognizedFace[]) {
    if (!this.canvasElement) return;

    const canvas = this.canvasElement.nativeElement;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    faces.forEach(face => {
      const [x1, y1, x2, y2] = face.bbox;
      const width = x2 - x1;
      const height = y2 - y1;

      // Color based on employee status
      const isUnknown = face.employee_code === 'Unknown';
      const boxColor = isUnknown ? '#f59e0b' : '#48bb78'; // Orange for Unknown, Green for Known
      const cornerColor = isUnknown ? '#d97706' : '#38a169';

      // Draw bounding box
      ctx.strokeStyle = boxColor;
      ctx.lineWidth = 3;
      ctx.strokeRect(x1, y1, width, height);

      // Draw label background (no % for Unknown)
      const label = isUnknown 
        ? face.employee_name 
        : `${face.employee_name} (${(face.confidence_score * 100).toFixed(1)}%)`;
      ctx.font = 'bold 16px Arial';
      const textMetrics = ctx.measureText(label);
      const textWidth = textMetrics.width;
      const textHeight = 20;

      ctx.fillStyle = boxColor;
      ctx.fillRect(x1, y1 - textHeight - 5, textWidth + 10, textHeight + 5);

      // Draw label text
      ctx.fillStyle = 'white';
      ctx.fillText(label, x1 + 5, y1 - 8);

      // Draw corner indicators (fancy UI)
      this.drawCorners(ctx, x1, y1, width, height, cornerColor);
    });
  }

  /**
   * Draw fancy corner indicators
   */
  drawCorners(ctx: CanvasRenderingContext2D, x: number, y: number, width: number, height: number, color: string = '#38a169') {
    const cornerLength = 20;
    ctx.strokeStyle = color;
    ctx.lineWidth = 4;

    // Top-left
    ctx.beginPath();
    ctx.moveTo(x, y + cornerLength);
    ctx.lineTo(x, y);
    ctx.lineTo(x + cornerLength, y);
    ctx.stroke();

    // Top-right
    ctx.beginPath();
    ctx.moveTo(x + width - cornerLength, y);
    ctx.lineTo(x + width, y);
    ctx.lineTo(x + width, y + cornerLength);
    ctx.stroke();

    // Bottom-left
    ctx.beginPath();
    ctx.moveTo(x, y + height - cornerLength);
    ctx.lineTo(x, y + height);
    ctx.lineTo(x + cornerLength, y + height);
    ctx.stroke();

    // Bottom-right
    ctx.beginPath();
    ctx.moveTo(x + width - cornerLength, y + height);
    ctx.lineTo(x + width, y + height);
    ctx.lineTo(x + width, y + height - cornerLength);
    ctx.stroke();
  }

  /**
   * Restart recognition
   */
  restart() {
    this.stopRecognition();
    setTimeout(() => this.startRecognition(), 500);
  }
}
