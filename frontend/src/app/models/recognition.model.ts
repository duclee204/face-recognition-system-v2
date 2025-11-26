export interface RecognitionFrame {
  type: 'frame' | 'info' | 'error' | 'camera_switched';
  frame?: string; // base64 image
  faces?: RecognizedFace[];
  timestamp?: string;
  process_time?: number;
  message?: string;
  camera_id?: number;
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

// ==================== AUTO REGISTRATION MODELS ====================

export interface AutoRegistrationStart {
  employee_code: string;
  full_name: string;
  email?: string;
  phone_number?: string;
  position?: string;
}

export interface AutoRegistrationProgress {
  session_id: string;
  employee_code: string;
  current_target_pose: string;
  captured_poses: string[];
  remaining_poses: string[];
  progress_percentage: number;
  is_complete: boolean;
}

export interface AutoRegistrationGuidance {
  type: 'guidance' | 'complete' | 'frame' | 'info' | 'error';
  status?: string;  // 'adjusting' | 'holding' | 'captured' | 'completed' | 'no_face' | 'multiple_faces'
  message: string;
  guidance?: string;
  pose_ok?: boolean;
  should_capture?: boolean;
  target_pose?: string;
  captured_pose?: string;
  yaw?: number;
  pitch?: number;
  roll?: number;
  stable_frames?: number;
  hold_frames_required?: number;
  progress?: AutoRegistrationProgress;
  frame_count?: number;
  image?: string;  // base64 frame preview
  captured_images?: string[];
}

export interface AutoRegistrationComplete {
  employee_code: string;
  session_id: string;
}

export interface AutoRegistrationCompleteResponse {
  success: boolean;
  message: string;
  employee_id?: number;
  total_images: number;
  embeddings_count: number;
}
