# 🚀 QUICK START GUIDE

## Bước 1: Cài đặt Dependencies

### 1.1 Cài Python 3.9+
Download tại: https://www.python.org/downloads/

### 1.2 Cài MySQL 8.0+
Download tại: https://dev.mysql.com/downloads/installer/

### 1.3 Verify installations
```powershell
python --version    # Should show 3.9+
mysql --version     # Should show 8.0+
```

## Bước 2: Setup Database

### 2.1 Mở MySQL Command Line
```powershell
mysql -u root -p
```

### 2.2 Tạo database
```sql
CREATE DATABASE face_recognition_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
exit;
```

## Bước 3: Setup Backend

### 3.1 Navigate to backend folder
```powershell
cd f:\Downloads\DACN AI\face-recognition-system\backend
```

### 3.2 Create virtual environment
```powershell
python -m venv venv
.\venv\Scripts\activate
```

### 3.3 Install dependencies
```powershell
pip install -r requirements.txt
```

**⏳ Lưu ý:** Quá trình này mất khoảng 5-10 phút!

### 3.4 Configure environment
```powershell
copy .env.example .env
notepad .env
```

Sửa các dòng sau trong `.env`:
```env
DB_PASSWORD=your_mysql_password_here
SECRET_KEY=your-secret-key-here-change-in-production
```

### 3.5 Initialize database tables
```powershell
python init_db.py
```

### 3.6 Run server
```powershell
python main.py
```

hoặc dùng script:
```powershell
start.bat
```

## Bước 4: Test API

### 4.1 Mở browser
Truy cập: **http://localhost:8000/docs**

### 4.2 Test endpoints
1. Click "GET /api/v1/system/status"
2. Click "Try it out"
3. Click "Execute"
4. Kiểm tra response

## Bước 5: Đăng ký nhân viên đầu tiên

### 5.1 Sử dụng Postman hoặc Swagger UI

#### Start registration:
```json
POST http://localhost:8000/api/v1/employees/register/start
Content-Type: application/json

{
  "employee_code": "EMP001",
  "full_name": "Nguyễn Văn A",
  "email": "nguyenvana@example.com",
  "department": "IT",
  "position": "Developer"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Registration session started...",
  "session_id": "EMP001_1234567890"
}
```

#### Upload frames (cần chương trình Python):
```python
# test_registration.py
import requests
import cv2
import base64
import time

session_id = "EMP001_1234567890"  # Từ response trên

cap = cv2.VideoCapture(0)
print("📸 Đang quét khuôn mặt... Xoay mặt vòng tròn!")

for i in range(100):
    ret, frame = cap.read()
    if not ret:
        break
    
    # Encode frame
    _, buffer = cv2.imencode('.jpg', frame)
    frame_base64 = base64.b64encode(buffer).decode()
    
    # Upload
    response = requests.post(
        f'http://localhost:8000/api/v1/employees/register/frame/{session_id}',
        json={
            "frame_data": frame_base64,
            "frame_number": i,
            "timestamp": time.time()
        }
    )
    
    print(f"Frame {i+1}/100 uploaded")
    time.sleep(0.05)

cap.release()
print("✅ Hoàn tất!")
```

#### Complete registration:
```json
POST http://localhost:8000/api/v1/employees/register/complete
Content-Type: application/json

{
  "session_id": "EMP001_1234567890"
}
```

### 5.2 Train model
```json
POST http://localhost:8000/api/v1/system/train-model
Content-Type: application/json

{
  "force_retrain": true
}
```

## Bước 6: Test nhận diện

### 6.1 Kiểm tra camera
```json
GET http://localhost:8000/api/v1/recognition/camera/info
```

### 6.2 Nhận diện qua WebSocket
Sử dụng test script:

```python
# test_recognition.py
import asyncio
import websockets
import json

async def test_stream():
    uri = "ws://localhost:8000/api/v1/recognition/ws/stream"
    
    print("🎥 Kết nối với camera stream...")
    
    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            
            if data['type'] == 'frame':
                faces = data.get('faces', [])
                if faces:
                    for face in faces:
                        print(f"✅ {face['employee_name']} - {face['confidence_score']:.3f}")

asyncio.run(test_stream())
```

## 🎉 Hoàn tất!

Bây giờ bạn có:
- ✅ Backend chạy tại http://localhost:8000
- ✅ API docs tại http://localhost:8000/docs
- ✅ Database đã setup
- ✅ Có thể đăng ký nhân viên
- ✅ Có thể nhận diện khuôn mặt

## 🔧 Các lệnh hữu ích

### Khởi động lại server
```powershell
cd backend
.\venv\Scripts\activate
python main.py
```

### Kiểm tra database
```powershell
mysql -u root -p face_recognition_db
SELECT * FROM employees;
SELECT * FROM attendance_logs;
```

### Xem logs
```powershell
# Logs được lưu trong backend/logs/
```

### Reset database
```powershell
mysql -u root -p
DROP DATABASE face_recognition_db;
CREATE DATABASE face_recognition_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
exit;

python init_db.py
```

## ⚠️ Troubleshooting

### "Module not found"
```powershell
pip install -r requirements.txt
```

### "Can't connect to MySQL"
- Kiểm tra MySQL đang chạy
- Verify password trong .env
- Test: `mysql -u root -p`

### "Camera not found"
```python
import cv2
cap = cv2.VideoCapture(0)
print('OK' if cap.isOpened() else 'FAIL')
```

### "InsightFace model not found"
Models sẽ tự động download lần đầu chạy. Chờ 2-3 phút.

## 📞 Support

- Issues: GitHub Issues
- Email: support@example.com
- Docs: http://localhost:8000/docs

---

**🎯 Tiếp theo:** Phát triển Angular Frontend!
