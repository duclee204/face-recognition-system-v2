# 🎯 Face Recognition System - Monolithic Application

**Hệ thống nhận diện khuôn mặt** với FastAPI tích hợp web interface - Kiến trúc Monolithic

## 🌟 Tính năng chính

### ✅ Đăng ký nhân viên với Multi-Pose Capture
- 🎯 **5 góc pose**: Center, Left, Right, Up, Down
- 🎥 Realtime head pose detection
- ⏱️ 30 stable frames/pose (3 giây)
- 💾 Lưu trữ embeddings 512-dim vào MySQL
- 🤖 Auto train SVM model sau khi hoàn thành

### ✅ Nhận diện thời gian thực
- ⚡ **10 FPS** realtime streaming qua WebSocket
- 🤖 SVM Classifier với InsightFace
- 📊 Bounding box overlay trên canvas
- 📝 Tự động chấm công khi nhận diện
- 🚫 Phát hiện Unknown faces

### ✅ Quản lý nhân viên
- 📋 Danh sách nhân viên với search/filter
- 🔍 Xem chi tiết thông tin
- ✏️ Cập nhật thông tin
- 🗑️ Xóa nhân viên
- 📊 Trạng thái trained/untrained

## 📋 Requirements

- Python 3.8+
- MySQL 8.0+
- Camera/Webcam
- Browser (Chrome/Firefox/Edge)

## 🚀 Installation

### 1. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 2. Setup MySQL Database

```sql
CREATE DATABASE face_recognition_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. Configure Environment

Edit `.env` or `app/core/config.py`:

```env
DATABASE_URL=mysql+pymysql://root:your_password@localhost:3306/face_recognition_db
```

### 4. Initialize Database

```powershell
python init_db.py
```

### 5. Run Application

```powershell
python main.py
```

### 6. Access Application

Open browser: **http://localhost:8000**
## 🏗️ Architecture

```
face-recognition-system/
├── app/
│   ├── static/           # CSS, JavaScript
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       ├── camera.js
│   │       └── api.js
│   ├── templates/        # HTML Pages
│   │   ├── index.html
│   │   ├── registration.html
│   │   ├── recognition.html
│   │   └── employees.html
│   ├── api/              # REST API endpoints
│   ├── core/             # Config & Database
│   ├── models/           # SQLAlchemy models
│   ├── services/         # Business logic
│   └── storage/          # File storage
├── insightface/          # AI models
├── main.py               # Entry point
├── init_db.py            # Database setup
├── requirements.txt      # Dependencies
└── README.md
```

## 💻 Tech Stack

- **Backend**: FastAPI + Jinja2 Templates
- **Frontend**: HTML5 + CSS3 + Vanilla JavaScript
- **Database**: MySQL 8.0 + SQLAlchemy
- **AI**: InsightFace + OpenCV + SVM
- **WebSocket**: Realtime recognition stream

## 📖 Usage Examples

### 1. Register New Employee (Circular Scanning)

```python
import requests
import cv2
import base64
import time

# Start registration
response = requests.post('http://localhost:8000/api/v1/employees/register/start', json={
    "employee_code": "EMP001",
    "full_name": "John Doe",
    "email": "john@example.com",
    "department": "Engineering"
})
session_id = response.json()['session_id']

# Capture video and send frames
cap = cv2.VideoCapture(0)
for i in range(100):  # Capture 100 frames while user rotates face
    ret, frame = cap.read()
    _, buffer = cv2.imencode('.jpg', frame)
    frame_base64 = base64.b64encode(buffer).decode()
    
    requests.post(f'http://localhost:8000/api/v1/employees/register/frame/{session_id}', json={
        "frame_data": frame_base64,
        "frame_number": i,
        "timestamp": time.time()
    })
    time.sleep(0.05)  # 20 FPS upload

cap.release()

# Complete registration
response = requests.post('http://localhost:8000/api/v1/employees/register/complete', json={
    "session_id": session_id
})
print(response.json())
```

## 📖 Usage Guide

### 1️⃣ Register Employee

1. Go to **http://localhost:8000/registration**
2. Fill employee information form
3. Click "Tạo nhân viên"
4. Allow camera access
5. Click "Bắt đầu chụp"
6. Perform 5 poses (3 seconds each):
   - 🎯 Center - Look straight
   - ⬅️ Left - Turn left ~30°
   - ➡️ Right - Turn right ~30°
   - ⬆️ Up - Look up ~30°
   - ⬇️ Down - Look down ~30°
7. Click "Huấn luyện mô hình"
8. Wait for training completion

### 2️⃣ Recognize Faces

1. Go to **http://localhost:8000/recognition**
2. Click "Bắt đầu"
3. System will automatically:
   - Detect faces with bounding boxes
   - Show employee name or "Unknown"
   - Log attendance
   - Update recognized list
4. Click "Dừng lại" to stop

### 3️⃣ Manage Employees

1. Go to **http://localhost:8000/employees**
2. View all employees
3. Search by name, ID, department
4. Click "Xem" for details
5. Click "Xóa" to delete

## 📡 API Endpoints

### HTML Pages
```
GET  /                    # Homepage
GET  /registration        # Employee registration
GET  /recognition         # Face recognition
GET  /employees           # Employee management
```

### API
```
GET    /api/employees              # List employees
POST   /api/employees              # Create employee
POST   /api/auto-registration/register-face  # Register face
POST   /api/head-pose/detect       # Detect head pose
WS     /api/recognition/ws/frontend-stream   # Recognition stream
GET    /api/attendance             # Attendance logs
GET    /docs                       # API Documentation
```

## 🔧 Configuration

Edit `app/core/config.py` or `.env`:

```env
# Database
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/face_recognition_db

# Recognition
RECOGNITION_THRESHOLD=0.5  # 0.4-0.6 recommended
SVM_C=10.0
SVM_GAMMA=0.1

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=True
```

## 🐛 Troubleshooting

### MySQL Connection Error
```powershell
net start MySQL80
mysql -u root -p
```

### Database Not Found
```sql
CREATE DATABASE face_recognition_db;
```

### Camera Not Working
- Allow camera in browser settings
- Close other apps using camera
- Works on localhost or HTTPS only

### Recognition Issues
- Lower RECOGNITION_THRESHOLD to 0.4
- Re-register with all 5 poses
- Ensure good lighting

## 📚 Documentation

- [Installation Guide](INSTALLATION_GUIDE.md)
- [Migration Report](MONOLITHIC_MIGRATION_REPORT.md)
- [API Docs](http://localhost:8000/docs)

## 📄 License

MIT License

## 👨‍💻 Author

Face Recognition System v2.0 - Monolithic Architecture

---

**Made with ❤️ using FastAPI + InsightFace**

🚀 **Quick Start**: `python main.py` → http://localhost:8000

3. Commit changes
4. Push to branch
5. Create Pull Request

## 📄 License

MIT License - See LICENSE file

## 👨‍💻 Author

Face Recognition Attendance System Team

---

🎉 **Happy Coding!**
