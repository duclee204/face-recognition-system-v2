# Auto Registration API - Đăng ký khuôn mặt tự động theo góc

## Tổng quan

API này cung cấp chức năng đăng ký khuôn mặt nhân viên tự động với việc thu thập ảnh từ nhiều góc độ khác nhau. Hệ thống tự động phát hiện hướng đầu (head pose) và chỉ chụp ảnh khi góc đạt chuẩn.

## Quy trình Auto Registration

```
1. Start Session → 2. WebSocket Stream → 3. Auto Capture → 4. Complete Registration
```

### Các góc cần thu thập:
1. **Center** - Mặt nhìn thẳng
2. **Left** - Quay đầu sang trái (yaw: -20° đến -50°)
3. **Right** - Quay đầu sang phải (yaw: 20° đến 50°)
4. **Up** - Ngẩng đầu lên (pitch: 10° đến 35°)
5. **Down** - Cúi đầu xuống (pitch: -10° đến -35°)

## Endpoints

### 1. Start Registration Session

**POST** `/api/v1/auto-registration/start`

Khởi tạo session đăng ký mới.

**Request:**
```json
{
  "employee_code": "EMP001",
  "full_name": "Nguyen Van A",
  "email": "a@company.com",
  "phone_number": "0123456789",
  "position": "Developer"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Auto registration session started",
  "session_id": "EMP001_1700000000",
  "employee_code": "EMP001",
  "progress": {
    "session_id": "EMP001_1700000000",
    "employee_code": "EMP001",
    "current_target_pose": "center",
    "captured_poses": [],
    "remaining_poses": ["center", "left", "right", "up", "down"],
    "progress_percentage": 0,
    "is_complete": false
  }
}
```

### 2. Get Progress

**GET** `/api/v1/auto-registration/progress/{employee_code}`

Kiểm tra tiến độ đăng ký.

**Response:**
```json
{
  "session_id": "EMP001_1700000000",
  "employee_code": "EMP001",
  "current_target_pose": "left",
  "captured_poses": ["center"],
  "remaining_poses": ["left", "right", "up", "down"],
  "progress_percentage": 20,
  "is_complete": false
}
```

### 3. WebSocket Auto Capture

**WebSocket** `/api/v1/auto-registration/ws/capture/{employee_code}`

Stream camera và tự động chụp khi góc đạt chuẩn.

**Messages từ Server:**

#### a) Guidance Message (Real-time feedback)
```json
{
  "type": "guidance",
  "status": "adjusting",  // adjusting | holding | captured | completed | no_face | multiple_faces
  "message": "Adjust your pose",
  "guidance": "Turn face slightly left",
  "pose_ok": false,
  "should_capture": false,
  "target_pose": "center",
  "yaw": -5.2,
  "pitch": 3.1,
  "roll": -1.8,
  "frame_count": 120
}
```

**Status types:**
- `no_face` - Không phát hiện khuôn mặt
- `multiple_faces` - Phát hiện nhiều hơn 1 khuôn mặt
- `adjusting` - Đang điều chỉnh góc (chưa đạt chuẩn)
- `holding` - Đang giữ góc đúng (đếm ngược)
- `captured` - Đã chụp thành công
- `completed` - Hoàn thành tất cả các góc

#### b) Holding Message (Đang giữ góc đúng)
```json
{
  "type": "guidance",
  "status": "holding",
  "message": "Hold steady... 12",
  "guidance": "Perfect! Hold steady... (12 frames left)",
  "pose_ok": true,
  "should_capture": false,
  "stable_frames": 3,
  "hold_frames_required": 15,
  "yaw": -0.5,
  "pitch": 2.1,
  "roll": 0.3,
  "frame_count": 145
}
```

#### c) Captured Message (Đã chụp)
```json
{
  "type": "guidance",
  "status": "captured",
  "message": "Captured center pose!",
  "guidance": "Perfect! Hold steady...",
  "pose_ok": true,
  "should_capture": true,
  "image_path": "/path/to/image.jpg",
  "captured_pose": "center",
  "yaw": 0.2,
  "pitch": 1.5,
  "roll": -0.5,
  "progress": {
    "captured_poses": ["center"],
    "remaining_poses": ["left", "right", "up", "down"],
    "progress_percentage": 20
  },
  "frame_count": 160
}
```

#### d) Complete Message
```json
{
  "type": "complete",
  "message": "All poses captured! Registration ready to finalize.",
  "progress": {
    "captured_poses": ["center", "left", "right", "up", "down"],
    "remaining_poses": [],
    "progress_percentage": 100,
    "is_complete": true
  },
  "captured_images": [
    "/path/to/center.jpg",
    "/path/to/left.jpg",
    "/path/to/right.jpg",
    "/path/to/up.jpg",
    "/path/to/down.jpg"
  ]
}
```

#### e) Frame Preview (Optional, every 5 frames)
```json
{
  "type": "frame",
  "image": "base64_encoded_jpeg_string",
  "frame_count": 150
}
```

### 4. Complete Registration

**POST** `/api/v1/auto-registration/complete`

Hoàn tất đăng ký - xử lý ảnh và tạo employee record.

**Request:**
```json
{
  "employee_code": "EMP001",
  "session_id": "EMP001_1700000000"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Employee registered successfully",
  "employee_id": 123,
  "total_images": 5,
  "embeddings_count": 5
}
```

### 5. Cancel Registration

**DELETE** `/api/v1/auto-registration/cancel/{employee_code}`

Hủy session đăng ký.

**Response:**
```json
{
  "success": true,
  "message": "Registration session cancelled"
}
```

### 6. Get Active Sessions

**GET** `/api/v1/auto-registration/active-sessions`

Lấy danh sách các session đang active.

**Response:**
```json
{
  "success": true,
  "active_sessions": ["EMP001", "EMP002"],
  "count": 2
}
```

## Flow diagram

```
Frontend                          Backend
   |                                |
   |--POST /start------------------>|
   |<------session_id---------------|
   |                                |
   |--WS /ws/capture--------------->|
   |                                |--- Open Camera
   |                                |--- Start Processing
   |                                |
   |<------guidance: adjusting------|
   |<------guidance: holding--------|
   |<------guidance: captured-------|
   |       (repeat for 5 poses)     |
   |                                |
   |<------complete-----------------|
   |                                |
   |--POST /complete--------------->|
   |                                |--- Process Images
   |                                |--- Extract Embeddings
   |                                |--- Create Employee
   |<------success------------------|
```

## Guidance Messages

### Center Pose
- ✅ "Perfect! Hold steady..."
- ❌ "Turn face slightly left/right"
- ❌ "Tilt head slightly up/down"
- ❌ "Keep head straight (don't tilt)"

### Left Pose
- ✅ "Perfect left angle! Hold steady..."
- ❌ "Turn head more to the LEFT"
- ❌ "Turn head less to the left"
- ❌ "Keep head level (don't look up/down)"

### Right Pose
- ✅ "Perfect right angle! Hold steady..."
- ❌ "Turn head more to the RIGHT"
- ❌ "Turn head less to the right"
- ❌ "Keep head level (don't look up/down)"

### Up Pose
- ✅ "Perfect up angle! Hold steady..."
- ❌ "Tilt head UP more"
- ❌ "Tilt head down slightly"
- ❌ "Keep face forward (don't turn left/right)"

### Down Pose
- ✅ "Perfect down angle! Hold steady..."
- ❌ "Tilt head DOWN more"
- ❌ "Tilt head up slightly"
- ❌ "Keep face forward (don't turn left/right)"

## Technical Details

### Head Pose Calculation
- **Yaw** (trục Y): Quay trái/phải (-90° to 90°)
  - Âm: Quay trái
  - Dương: Quay phải
  
- **Pitch** (trục X): Ngẩng/cúi (-90° to 90°)
  - Âm: Cúi xuống
  - Dương: Ngẩng lên
  
- **Roll** (trục Z): Nghiêng (-180° to 180°)
  - Độ nghiêng đầu sang trái/phải

### Auto Capture Logic
1. Phát hiện khuôn mặt từ InsightFace
2. Trích xuất facial landmarks
3. Tính toán head pose (yaw, pitch, roll) bằng PnP algorithm
4. Kiểm tra góc có đạt chuẩn với target pose
5. Đếm 15 frames ổn định (0.5s @ 30fps)
6. Tự động chụp và lưu ảnh
7. Chuyển sang góc tiếp theo

### Thresholds
- **Yaw threshold**: ±15° (cho center, up, down)
- **Pitch threshold**: ±15° (cho center, left, right)
- **Roll threshold**: ±15° (cho tất cả poses)
- **Hold frames**: 15 frames (~0.5 giây)

## Error Handling

### Common Errors
- **400 Bad Request**: Employee code đã tồn tại
- **404 Not Found**: Session không tồn tại
- **500 Internal Server Error**: Lỗi xử lý

### WebSocket Errors
```json
{
  "type": "error",
  "message": "Failed to open camera"
}
```

## Testing

### Test với curl:

```bash
# 1. Start session
curl -X POST http://localhost:8000/api/v1/auto-registration/start \
  -H "Content-Type: application/json" \
  -d '{"employee_code": "TEST001", "full_name": "Test User"}'

# 2. Check progress
curl http://localhost:8000/api/v1/auto-registration/progress/TEST001

# 3. WebSocket (use wscat or JavaScript)
wscat -c ws://localhost:8000/api/v1/auto-registration/ws/capture/TEST001
```

## Frontend Integration

### JavaScript WebSocket Example:

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/auto-registration/ws/capture/EMP001');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch(data.type) {
    case 'guidance':
      updateGuidanceUI(data);
      if (data.pose_ok) {
        showGreenBorder();
      } else {
        showRedBorder();
      }
      break;
      
    case 'complete':
      showSuccessMessage();
      finishRegistration();
      break;
      
    case 'frame':
      updateCameraPreview(data.image);
      break;
  }
};

function updateGuidanceUI(data) {
  document.getElementById('status').textContent = data.message;
  document.getElementById('guidance').textContent = data.guidance;
  document.getElementById('progress').textContent = 
    `${data.progress?.progress_percentage || 0}%`;
}
```

## Notes

- Camera cần được mở trước khi gọi WebSocket
- Mỗi employee chỉ có 1 active session
- Session tự động cleanup khi complete hoặc cancel
- Images được lưu tại `app/storage/employee_images/{employee_code}/{session_id}/`
- Landmarks sử dụng từ InsightFace (106 points hoặc 5 points)
- Frame rate: ~30fps với frame preview mỗi 5 frames (giảm bandwidth)
