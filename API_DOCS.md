# 📡 API Documentation

## Base URL
```
http://localhost:8000
```

## Authentication
Currently no authentication required (add JWT in production)

---

## 👥 Employees API

### 1. Start Registration (Circular Scan)

**Endpoint:** `POST /api/v1/employees/register/start`

**Description:** Bắt đầu quá trình đăng ký nhân viên mới với circular face scanning

**Request Body:**
```json
{
  "employee_code": "EMP001",
  "full_name": "Nguyễn Văn A",
  "email": "nguyenvana@example.com",
  "phone": "0912345678",
  "department": "IT",
  "position": "Developer"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Registration session started. Please scan face in circular motion.",
  "session_id": "EMP001_1699999999"
}
```

---

### 2. Upload Registration Frame

**Endpoint:** `POST /api/v1/employees/register/frame/{session_id}`

**Description:** Upload frame trong quá trình quét vòng tròn

**Request Body:**
```json
{
  "frame_data": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "frame_number": 1,
  "timestamp": 1699999999.123
}
```

**Response:**
```json
{
  "success": true,
  "frames_collected": 50,
  "message": "Frame received"
}
```

**Note:** Gửi ~100 frames trong 5-10 giây

---

### 3. Complete Registration

**Endpoint:** `POST /api/v1/employees/register/complete`

**Description:** Hoàn tất đăng ký và xử lý tất cả frames

**Request Body:**
```json
{
  "session_id": "EMP001_1699999999"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Registration completed successfully. 150 embeddings created.",
  "employee_id": 1,
  "total_embeddings": 150,
  "processing_time": 3.45
}
```

---

### 4. Get Employees List

**Endpoint:** `GET /api/v1/employees`

**Query Parameters:**
- `skip`: Pagination offset (default: 0)
- `limit`: Results per page (default: 100)
- `is_active`: Filter by active status (optional)

**Response:**
```json
{
  "total": 10,
  "employees": [
    {
      "id": 1,
      "employee_code": "EMP001",
      "full_name": "Nguyễn Văn A",
      "email": "nguyenvana@example.com",
      "phone": "0912345678",
      "department": "IT",
      "position": "Developer",
      "total_embeddings": 150,
      "is_active": true,
      "created_at": "2024-01-01T10:00:00",
      "updated_at": "2024-01-01T10:00:00"
    }
  ]
}
```

---

### 5. Get Employee Details

**Endpoint:** `GET /api/v1/employees/{employee_id}`

**Response:**
```json
{
  "id": 1,
  "employee_code": "EMP001",
  "full_name": "Nguyễn Văn A",
  "email": "nguyenvana@example.com",
  "total_embeddings": 150,
  "is_active": true,
  "created_at": "2024-01-01T10:00:00"
}
```

---

## 🎥 Recognition API

### 1. Recognize Single Frame

**Endpoint:** `POST /api/v1/recognition/recognize`

**Description:** Nhận diện khuôn mặt trong 1 frame

**Request Body:**
```json
{
  "frame_data": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "threshold": 0.5
}
```

**Response:**
```json
{
  "success": true,
  "faces": [
    {
      "employee_id": 1,
      "employee_code": "EMP001",
      "employee_name": "Nguyễn Văn A",
      "confidence_score": 0.876,
      "recognition_method": "svm",
      "bbox": [100, 150, 300, 400]
    }
  ],
  "processing_time": 0.045,
  "timestamp": "2024-01-01T10:30:00"
}
```

---

### 2. WebSocket Real-time Stream

**Endpoint:** `WS /api/v1/recognition/ws/stream`

**Description:** Streaming camera với nhận diện realtime (60 FPS)

**Client → Server:** Không cần gửi gì (server tự đọc camera)

**Server → Client Messages:**

#### Frame Message:
```json
{
  "type": "frame",
  "frame": "base64_encoded_jpeg",
  "faces": [
    {
      "employee_id": 1,
      "employee_code": "EMP001",
      "employee_name": "Nguyễn Văn A",
      "confidence_score": 0.876,
      "recognition_method": "svm",
      "bbox": [100, 150, 300, 400]
    }
  ],
  "timestamp": "2024-01-01T10:30:00.123",
  "process_time": 45.5
}
```

#### Info Message:
```json
{
  "type": "info",
  "message": "Camera stream started"
}
```

#### Error Message:
```json
{
  "type": "error",
  "message": "Failed to start camera"
}
```

**Usage Example (JavaScript):**
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/recognition/ws/stream');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'frame') {
    // Display frame
    document.getElementById('video').src = 'data:image/jpeg;base64,' + data.frame;
    
    // Show recognized faces
    data.faces.forEach(face => {
      console.log(`✅ ${face.employee_name} - ${face.confidence_score.toFixed(3)}`);
    });
  }
};
```

---

### 3. Get Camera Info

**Endpoint:** `GET /api/v1/recognition/camera/info`

**Response:**
```json
{
  "available": true,
  "width": 640,
  "height": 480,
  "fps": 30,
  "backend": "DSHOW"
}
```

---

## 📊 Attendance API

### 1. Get Attendance Logs

**Endpoint:** `GET /api/v1/attendance/logs`

**Query Parameters:**
- `skip`: Pagination offset
- `limit`: Results per page
- `employee_id`: Filter by employee
- `start_date`: Filter from date (ISO format)
- `end_date`: Filter to date (ISO format)

**Example:**
```
GET /api/v1/attendance/logs?employee_id=1&start_date=2024-01-01T00:00:00&limit=50
```

**Response:**
```json
{
  "total": 120,
  "logs": [
    {
      "id": 1,
      "employee_id": 1,
      "employee_code": "EMP001",
      "employee_name": "Nguyễn Văn A",
      "confidence_score": 0.876,
      "recognition_method": "svm",
      "check_in_time": "2024-01-01T08:30:15"
    }
  ]
}
```

---

### 2. Get Today's Attendance

**Endpoint:** `GET /api/v1/attendance/today`

**Response:**
```json
{
  "success": true,
  "date": "2024-01-01",
  "total": 15,
  "logs": [...]
}
```

---

### 3. Get Attendance Statistics

**Endpoint:** `GET /api/v1/attendance/stats`

**Response:**
```json
{
  "total_today": 15,
  "total_this_week": 87,
  "total_this_month": 320,
  "unique_employees_today": 15
}
```

---

### 4. Check Employee Check-in Status

**Endpoint:** `GET /api/v1/attendance/check-in-status/{employee_id}`

**Response:**
```json
{
  "success": true,
  "employee_id": 1,
  "has_checked_in_today": true,
  "date": "2024-01-01"
}
```

---

## ⚙️ System API

### 1. Get System Status

**Endpoint:** `GET /api/v1/system/status`

**Response:**
```json
{
  "status": "operational",
  "total_employees": 25,
  "model_loaded": true,
  "insightface_loaded": true,
  "camera_available": true,
  "last_trained": null
}
```

---

### 2. Train SVM Model

**Endpoint:** `POST /api/v1/system/train-model`

**Description:** Train lại SVM classifier (cần gọi sau khi thêm nhân viên mới)

**Request Body:**
```json
{
  "force_retrain": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Model trained successfully on 25 employees",
  "training_time": 7.89,
  "model_accuracy": 0.973,
  "total_samples": 3750
}
```

---

### 3. Reload Models

**Endpoint:** `POST /api/v1/system/reload-models`

**Description:** Reload database và models từ disk

**Response:**
```json
{
  "success": true,
  "message": "Models reloaded successfully",
  "employees_loaded": 25,
  "model_loaded": true
}
```

---

### 4. Health Check

**Endpoint:** `GET /api/v1/system/health`

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T10:30:00"
}
```

---

## 🔧 Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid image data"
}
```

### 404 Not Found
```json
{
  "detail": "Employee not found"
}
```

### 500 Internal Server Error
```json
{
  "success": false,
  "message": "Internal server error",
  "detail": "Error description"
}
```

---

## 📝 Notes

- Tất cả timestamps sử dụng ISO 8601 format
- Base64 images có thể bao gồm prefix `data:image/jpeg;base64,` hoặc không
- Threshold mặc định: 0.5 (có thể điều chỉnh 0.3-0.7)
- WebSocket tự động reconnect nếu mất kết nối
- Attendance chỉ log 1 lần/ngày cho mỗi nhân viên

---

## 🎯 Recommended Flow

1. **Initial Setup:**
   - Check system status
   - Verify camera availability

2. **Register Employees:**
   - Start registration
   - Collect 80-120 frames (circular scan)
   - Complete registration
   - Train model

3. **Recognition:**
   - Connect WebSocket stream
   - Display video + recognized faces
   - Auto-log attendance

4. **Reporting:**
   - Query attendance logs
   - Generate statistics
   - Export data

---

**💡 Tip:** Sử dụng Swagger UI tại http://localhost:8000/docs để test API interactively!
