export interface RecognitionFrame {
  type: 'frame' | 'info' | 'error';
  frame?: string; // base64 image
  faces?: RecognizedFace[];
  timestamp?: string;
  process_time?: number;
  message?: string;
}

export interface RecognizedFace {
  employee_id: number;
  employee_code: string;
  employee_name: string;
  confidence_score: number;
  recognition_method: string;
  bbox: number[]; // [x1, y1, x2, y2]
}

export interface RegistrationSession {
  success: boolean;
  message: string;
  session_id: string;
}

export interface RegistrationFrame {
  frame_data: string; // base64 image with prefix
  frame_number: number;
  timestamp: number;
}

export interface RegistrationComplete {
  success: boolean;
  message: string;
  employee_id: number;
  total_embeddings: number;
  processing_time: number;
}
