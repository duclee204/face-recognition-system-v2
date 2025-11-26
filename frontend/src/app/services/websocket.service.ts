import { Injectable } from '@angular/core';
import { Observable, Subject } from 'rxjs';
import { RecognitionFrame } from '../models/recognition.model';

@Injectable({
  providedIn: 'root'
})
export class WebsocketService {
  private ws: WebSocket | null = null;
  private frameSubject = new Subject<RecognitionFrame>();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 3000;

  constructor() { }

  /**
   * Connect to WebSocket stream
   */
  connect(url: string = 'ws://localhost:8000/api/v1/recognition/ws/stream'): Observable<RecognitionFrame> {
    if (this.ws) {
      this.disconnect();
    }

    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      console.log('✅ WebSocket connected');
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      try {
        const data: RecognitionFrame = JSON.parse(event.data);
        this.frameSubject.next(data);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    this.ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
      this.frameSubject.next({
        type: 'error',
        message: 'WebSocket connection error'
      });
    };

    this.ws.onclose = (event) => {
      console.log('🔌 WebSocket disconnected');
      
      // Auto reconnect if not manual close
      if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectAttempts++;
        console.log(`🔄 Reconnecting (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
        
        setTimeout(() => {
          this.connect(url);
        }, this.reconnectDelay);
      }
    };

    return this.frameSubject.asObservable();
  }

  /**
   * Disconnect WebSocket
   */
  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
      this.reconnectAttempts = this.maxReconnectAttempts; // Prevent auto reconnect
    }
  }

  /**
   * Check if WebSocket is connected
   */
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  /**
   * Get connection state
   */
  getState(): number | null {
    return this.ws?.readyState ?? null;
  }

  /**
   * Send message to WebSocket
   */
  sendMessage(message: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.error('WebSocket is not connected');
    }
  }

  /**
   * Switch camera
   */
  switchCamera(cameraId: number): void {
    this.sendMessage({
      type: 'switch_camera',
      camera_id: cameraId
    });
  }
}
