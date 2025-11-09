# Face Recognition Attendance System - Backend

🎯 **FastAPI Backend** for Face Recognition Attendance System with InsightFace, SVM, and Multiprocessing

## 🌟 Features

- ✅ **Employee Registration** - Circular face scanning like iPhone Face ID
- ✅ **Real-time Recognition** - 60 FPS with multiprocessing
- ✅ **SVM Classifier** - GridSearchCV optimized
- ✅ **Cosine Similarity Fallback** - Dual recognition methods
- ✅ **MySQL Database** - Full employee and attendance management
- ✅ **WebSocket Streaming** - Real-time camera feed
- ✅ **REST API** - Complete CRUD operations
- ✅ **Data Augmentation** - Albumentations for robust training
- ✅ **Attendance Logging** - Automatic check-in tracking

## 📋 Requirements

- Python 3.9+
- MySQL 8.0+
- Camera/Webcam
- CPU (GPU optional)

## 🚀 Installation

### 1. Create Virtual Environment

```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
```

### 2. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 3. Setup MySQL Database

```sql
CREATE DATABASE face_recognition_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 4. Configure Environment

Copy `.env.example` to `.env` and update:

```env
DATABASE_URL=mysql+pymysql://root:your_password@localhost:3306/face_recognition_db
DB_PASSWORD=your_password
SECRET_KEY=your-secret-key-here
```

### 5. Download InsightFace Models

Models will be auto-downloaded on first run, or manually:

```powershell
python -c "from insightface.app import FaceAnalysis; app = FaceAnalysis(name='antelopev2'); app.prepare(ctx_id=0)"
```

### 6. Run Database Migrations

```powershell
python -c "from app.core.database import init_db; init_db()"
```

## 🏃 Running the Server

### Development Mode

```powershell
python main.py
```

or with uvicorn directly:

```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```powershell
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📡 API Endpoints

### Base URL
```
http://localhost:8000
```

### API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Endpoints Overview

#### 👥 Employees
- `POST /api/v1/employees/register/start` - Start registration
- `POST /api/v1/employees/register/frame/{session_id}` - Upload frame
- `POST /api/v1/employees/register/complete` - Complete registration
- `GET /api/v1/employees` - List employees
- `GET /api/v1/employees/{id}` - Get employee
- `PUT /api/v1/employees/{id}` - Update employee
- `DELETE /api/v1/employees/{id}` - Delete employee

#### 🎥 Recognition
- `POST /api/v1/recognition/recognize` - Recognize single frame
- `WS /api/v1/recognition/ws/stream` - Real-time WebSocket stream
- `GET /api/v1/recognition/camera/info` - Camera info
- `GET /api/v1/recognition/recognized` - Get recognized list

#### 📊 Attendance
- `GET /api/v1/attendance/logs` - Get attendance logs
- `GET /api/v1/attendance/today` - Today's attendance
- `GET /api/v1/attendance/stats` - Statistics
- `GET /api/v1/attendance/employee/{id}` - Employee attendance
- `GET /api/v1/attendance/check-in-status/{id}` - Check-in status

#### ⚙️ System
- `GET /api/v1/system/status` - System status
- `POST /api/v1/system/train-model` - Train SVM model
- `POST /api/v1/system/reload-models` - Reload models
- `GET /api/v1/system/health` - Health check
- `GET /api/v1/system/info` - System info

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

### 2. Train Model After Registration

```python
response = requests.post('http://localhost:8000/api/v1/system/train-model', json={
    "force_retrain": True
})
print(response.json())
```

### 3. Real-time Recognition (WebSocket)

```python
import asyncio
import websockets
import json

async def recognize_stream():
    uri = "ws://localhost:8000/api/v1/recognition/ws/stream"
    
    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            
            if data['type'] == 'frame':
                faces = data['faces']
                for face in faces:
                    print(f"✅ {face['employee_name']} - {face['confidence_score']:.3f}")

asyncio.run(recognize_stream())
```

## 🏗️ Architecture

```
backend/
├── app/
│   ├── api/              # API endpoints
│   │   ├── employees.py  # Employee registration
│   │   ├── recognition.py # Face recognition
│   │   ├── attendance.py  # Attendance logging
│   │   └── system.py      # System management
│   ├── core/             # Core configuration
│   │   ├── config.py     # Settings
│   │   └── database.py   # Database connection
│   ├── models/           # Database models
│   │   ├── employee.py   # Employee model
│   │   ├── attendance.py # Attendance model
│   │   └── schemas.py    # Pydantic schemas
│   ├── services/         # Business logic
│   │   ├── face_recognition.py # InsightFace + SVM
│   │   ├── camera.py     # Camera multiprocessing
│   │   ├── employee.py   # Employee CRUD
│   │   └── attendance.py # Attendance logging
│   └── storage/          # File storage
│       ├── employee_images/
│       ├── models/       # SVM, embeddings
│       └── insightface_models/
├── main.py               # FastAPI app
├── requirements.txt      # Dependencies
└── .env                  # Configuration
```

## 🔧 Configuration

### Key Settings (`.env`)

```env
# Recognition
RECOGNITION_THRESHOLD=0.5  # Lower = easier to recognize
AUGMENTATION_COUNT=5       # Augmented samples per frame
SVM_KERNEL=rbf
SVM_C=10
SVM_GAMMA=0.1

# Camera
CAMERA_WIDTH=640
CAMERA_HEIGHT=480
PREDICT_INTERVAL=30  # Process every N frames (30 = 1 sec at 30 FPS)
```

## 🧪 Testing

Run API tests:

```powershell
pytest tests/ -v
```

## 📝 Database Schema

### Employees Table
- `id` - Primary key
- `employee_code` - Unique code
- `full_name` - Employee name
- `email` - Email address
- `embeddings` - JSON face embeddings
- `mean_embedding` - Average embedding
- `total_embeddings` - Count
- `is_active` - Active status
- `created_at` / `updated_at` - Timestamps

### Attendance Logs Table
- `id` - Primary key
- `employee_id` - Foreign key
- `confidence_score` - Recognition confidence
- `recognition_method` - 'svm' or 'cosine'
- `check_in_time` - Timestamp
- `snapshot_path` - Image path (optional)

## 🎯 Performance

- **Registration**: ~3-5 seconds for 100 frames
- **Training**: ~5-10 seconds for 50 employees
- **Recognition**: <50ms per frame (with SVM)
- **Streaming**: 60 FPS (multiprocessing)

## 🐛 Troubleshooting

### Camera not found
```powershell
# Test camera
python -c "import cv2; cap = cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'FAIL')"
```

### InsightFace model not loading
```powershell
# Re-download models
rm -rf ./app/storage/insightface_models
python -c "from insightface.app import FaceAnalysis; FaceAnalysis(name='antelopev2').prepare(ctx_id=0)"
```

### Database connection error
- Check MySQL is running
- Verify credentials in `.env`
- Test connection: `mysql -u root -p`

## 📚 Documentation

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [InsightFace](https://github.com/deepinsight/insightface)
- [Scikit-learn SVM](https://scikit-learn.org/stable/modules/svm.html)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## 📄 License

MIT License - See LICENSE file

## 👨‍💻 Author

Face Recognition Attendance System Team

---

🎉 **Happy Coding!**
