import { Injectable } from '@angular/core';
import { Observable, Subject } from 'rxjs';
import { AutoRegistrationGuidance } from '../models/recognition.model';

@Injectable({
  providedIn: 'root'
})
export class AutoRegistrationWebSocketService {
  private socket?: WebSocket;
  private messageSubject = new Subject<AutoRegistrationGuidance>();

  /**
   * Connect to auto registration WebSocket
   */
  connect(employeeCode: string, url?: string): Observable<AutoRegistrationGuidance> {
    const wsUrl = url || `ws://localhost:8000/api/v1/auto-registration/ws/capture/${employeeCode}`;

    this.socket = new WebSocket(wsUrl);

    this.socket.onopen = () => {
      console.log('Auto Registration WebSocket connected');
    };

    this.socket.onmessage = (event) => {
      try {
        const data: AutoRegistrationGuidance = JSON.parse(event.data);
        this.messageSubject.next(data);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    this.socket.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.messageSubject.error(error);
    };

    this.socket.onclose = () => {
      console.log('Auto Registration WebSocket closed');
      this.messageSubject.complete();
    };

    return this.messageSubject.asObservable();
  }

  /**
   * Send message to server (if needed)
   */
  send(message: any): void {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(message));
    }
  }

  /**
   * Disconnect WebSocket
   */
  disconnect(): void {
    if (this.socket) {
      this.socket.close();
      this.socket = undefined;
    }
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.socket !== undefined && this.socket.readyState === WebSocket.OPEN;
  }
}
