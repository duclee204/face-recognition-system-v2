# 📹 Hướng Dẫn Chuyển Đổi Camera

## Tổng Quan
Hệ thống hỗ trợ chuyển đổi camera động trong quá trình nhận diện khuôn mặt thông qua WebSocket.

## Tính Năng

### Backend Features
1. **Camera Service** - Quản lý camera
   - Mở/đóng camera
   - Chuyển đổi camera động
   - Liệt kê camera khả dụng
   - Đọc frame từ camera

2. **WebSocket Stream** - Streaming real-time
   - Nhận frame từ camera
   - Gửi message điều khiển từ client
   - Xử lý lệnh chuyển camera
   - Trả về thông báo trạng thái

3. **REST API Endpoints**
   - `GET /api/v1/recognition/camera/list` - Danh sách camera
   - `GET /api/v1/recognition/camera/info` - Thông tin camera hiện tại
   - `GET /api/v1/recognition/recognized` - Danh sách nhân viên đã nhận diện

### Frontend Features
1. **Camera Selector** - Dropdown chọn camera
2. **Real-time Switching** - Chuyển camera không cần reload
3. **Status Display** - Hiển thị camera đang sử dụng
4. **Auto-detect** - Tự động phát hiện camera khả dụng

## Cách Sử Dụng

### 1. Khởi Động Backend
```bash
cd face-recognition-system/backend
python -m uvicorn app.main:app --reload
```

### 2. Khởi Động Frontend
```bash
cd face-recognition-system/frontend
npm start
```

### 3. Sử dụng giao diện
1. Mở trình duyệt: `http://localhost:4200`
2. Vào trang **Recognition**
3. Chọn camera từ dropdown
4. Click **Start Recognition**
5. Đổi camera bất cứ lúc nào bằng dropdown

## WebSocket Protocol

### Message Format

#### 1. Client → Server (Switch Camera)
```json
{
  "type": "switch_camera",
  "camera_id": 1
}
```

#### 2. Server → Client (Camera Switched)
```json
{
  "type": "camera_switched",
  "camera_id": 1,
  "message": "Switched to camera 1"
}
```

#### 3. Server → Client (Frame + Camera ID)
```json
{
  "type": "frame",
  "frame": "base64_image_data",
  "faces": [...],
  "camera_id": 1,
  "timestamp": "2025-11-09T10:30:00"
}
```

#### 4. Server → Client (Error)
```json
{
  "type": "error",
  "message": "Failed to switch to camera 1"
}
```

## API Endpoints

### 1. Liệt Kê Camera
```http
GET /api/v1/recognition/camera/list
```

**Response:**
```json
{
  "success": true,
  "cameras": [
    {
      "id": 0,
      "name": "Integrated Camera",
      "available": true
    },
    {
      "id": 1,
      "name": "USB Camera",
      "available": true
    }
  ],
  "count": 2
}
```

### 2. Thông Tin Camera
```http
GET /api/v1/recognition/camera/info
```

**Response:**
```json
{
  "available": true,
  "camera_id": 0,
  "width": 640,
  "height": 480,
  "fps": 30
}
```

### 3. Nhân Viên Đã Nhận Diện
```http
GET /api/v1/recognition/recognized
```

**Response:**
```json
{
  "success": true,
  "recognized": [
    {
      "employee_code": "EMP001",
      "employee_name": "Nguyễn Văn A",
      "confidence_score": 0.95,
      "timestamp": "2025-11-09T10:30:00"
    }
  ],
  "count": 1
}
```

## Code Examples

### Backend - Camera Service
```python
# app/services/camera.py
class CameraService:
    def switch_camera(self, camera_id: int) -> bool:
        """Switch to different camera"""
        if self.cap:
            self.cap.release()
        
        self.camera_id = camera_id
        return self.open_camera()
    
    def list_available_cameras(self, max_test: int = 10):
        """List all available cameras"""
        available_cameras = []
        for i in range(max_test):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available_cameras.append({
                    "id": i,
                    "name": f"Camera {i}",
                    "available": True
                })
                cap.release()
        return available_cameras
```

### Backend - WebSocket Handler
```python
@router.websocket("/ws/stream")
async def websocket_recognition_stream(websocket: WebSocket):
    await websocket.accept()
    
    # Receive messages from client
    async def receive_messages():
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "switch_camera":
                camera_id = message.get("camera_id")
                success = camera_service.switch_camera(camera_id)
                
                if success:
                    await websocket.send_json({
                        "type": "camera_switched",
                        "camera_id": camera_id
                    })
```

### Frontend - WebSocket Service
```typescript
// services/websocket.service.ts
export class WebsocketService {
  switchCamera(cameraId: number): void {
    this.sendMessage({
      type: 'switch_camera',
      camera_id: cameraId
    });
  }
  
  sendMessage(message: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }
}
```

### Frontend - Component
```typescript
// components/recognition.component.ts
export class RecognitionComponent {
  availableCameras: any[] = [];
  selectedCameraId: number = 0;
  
  loadCameras() {
    this.apiService.listCameras().subscribe({
      next: (response) => {
        this.availableCameras = response.cameras;
      }
    });
  }
  
  onCameraChange(event: any) {
    this.selectedCameraId = parseInt(event.target.value, 10);
    if (this.isConnected) {
      this.wsService.switchCamera(this.selectedCameraId);
    }
  }
}
```

### Frontend - Template
```html
<!-- Camera Selector -->
<div class="camera-selector">
  <label>📷 Camera:</label>
  <select [(ngModel)]="selectedCameraId" (change)="onCameraChange($event)">
    <option *ngFor="let camera of availableCameras" [value]="camera.id">
      {{ camera.name }} ({{ camera.id }})
    </option>
  </select>
  <span class="current-camera" *ngIf="isStreaming">
    📹 Current: Camera {{ currentCameraId }}
  </span>
</div>
```

## Kiểm Tra Camera

### Python Script
```python
import cv2

def test_cameras(max_test=10):
    """Test all available cameras"""
    for i in range(max_test):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            print(f"✅ Camera {i} is available")
            ret, frame = cap.read()
            if ret:
                print(f"   Resolution: {frame.shape[1]}x{frame.shape[0]}")
            cap.release()
        else:
            print(f"❌ Camera {i} not available")

if __name__ == "__main__":
    test_cameras()
```

### Command Line (Windows)
```powershell
# List cameras using Python
python -c "import cv2; [print(f'Camera {i}: {'OK' if cv2.VideoCapture(i).isOpened() else 'FAIL'}') for i in range(5)]"
```

## Troubleshooting

### Lỗi Camera Không Mở Được
```python
# Kiểm tra quyền truy cập camera
import cv2
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Cannot open camera - Check permissions")
```

### Lỗi WebSocket Disconnect
- Kiểm tra backend đang chạy
- Kiểm tra URL WebSocket: `ws://localhost:8000/api/v1/recognition/ws/stream`
- Xem console log để debug

### Camera Đang Được Sử Dụng
- Đóng ứng dụng khác đang dùng camera
- Restart backend service
- Thử camera ID khác

## Performance Tips

1. **Frame Rate** - Giảm FPS nếu cần:
   ```python
   await asyncio.sleep(0.033)  # ~30 FPS
   await asyncio.sleep(0.066)  # ~15 FPS
   ```

2. **Resolution** - Giảm độ phân giải:
   ```python
   cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
   cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
   ```

3. **Background Processing** - AI worker chạy riêng thread
   ```python
   ai_thread = threading.Thread(target=ai_worker, daemon=True)
   ai_thread.start()
   ```

## Kết Luận
Hệ thống đã hỗ trợ đầy đủ tính năng chuyển đổi camera động qua WebSocket với giao diện thân thiện và hiệu suất cao! 🚀
