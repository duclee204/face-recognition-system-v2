# 🎯 Face Recognition Attendance System

**Hệ thống điểm danh nhận diện khuôn mặt chuyên nghiệp** với Backend FastAPI và Frontend Angular

## 🌟 Tính năng chính

### ✅ Đăng ký nhân viên (Face ID Style)
- ✨ **Quét vòng tròn** như iPhone Face ID
- 🎥 Tự động trích xuất nhiều góc độ từ video
- 🔄 Data augmentation với Albumentations
- 💾 Lưu trữ embeddings 512-dim vào MySQL

### ✅ Nhận diện thời gian thực
- ⚡ **60 FPS** với multiprocessing (tách 2 process)
- 🤖 SVM Classifier + Cosine Similarity fallback
- 📊 Hiển thị tên và độ chính xác trên FE
- 🚫 Không hiển thị nếu không có trong database

### ✅ Quản lý điểm danh
- 📝 Tự động ghi log khi nhận diện
- 📅 Chỉ điểm danh 1 lần/ngày
- 📊 Thống kê theo ngày/tuần/tháng
- 🔍 Tra cứu lịch sử điểm danh

## 🏗️ Kiến trúc hệ thống

```
face-recognition-system/
├── backend/              # FastAPI Backend
│   ├── app/
│   │   ├── api/         # REST API endpoints
│   │   ├── core/        # Config & Database
│   │   ├── models/      # SQLAlchemy models
│   │   ├── services/    # Business logic
│   │   │   ├── face_recognition.py  # InsightFace + SVM
│   │   │   ├── camera.py            # Multiprocessing camera
│   │   │   ├── employee.py          # Employee CRUD
│   │   │   └── attendance.py        # Attendance logging
│   │   └── storage/     # File storage
│   ├── main.py          # FastAPI app
│   └── requirements.txt
│
└── frontend/            # Angular Frontend (coming next)
    ├── src/
    │   ├── app/
    │   │   ├── components/
    │   │   │   ├── registration/    # Circular face scan
    │   │   │   ├── recognition/     # Real-time stream
    │   │   │   ├── employee-list/   # Employee management
    │   │   │   └── attendance/      # Attendance logs
    │   │   ├── services/
    │   │   └── models/
    │   └── assets/
    └── package.json
```

## 💻 Công nghệ sử dụng

### Backend
- **FastAPI** - Modern Python web framework
- **InsightFace** - Face detection & embedding extraction (512-dim)
- **OpenCV** - Image processing & camera
- **Scikit-learn** - SVM classifier with GridSearchCV
- **Albumentations** - Data augmentation
- **SQLAlchemy** - ORM for MySQL
- **Multiprocessing** - 60 FPS performance

### Frontend (Angular)
- **Angular 17+** - Modern TypeScript framework
- **WebSocket** - Real-time camera streaming
- **Angular Material** - UI components
- **RxJS** - Reactive programming
- **Chart.js** - Statistics visualization

## 🚀 Quick Start

### 1️⃣ Setup Backend

```powershell
cd backend

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup MySQL database
mysql -u root -p < database_setup.sql

# Configure environment
copy .env.example .env
# Edit .env with your MySQL credentials

# Initialize database
python init_db.py

# Run server
python main.py
```

Backend sẽ chạy tại: **http://localhost:8000**

API Docs: **http://localhost:8000/docs**

### 2️⃣ Setup Frontend

```powershell
cd frontend

# Install dependencies
npm install

# Run development server
ng serve
```

Frontend sẽ chạy tại: **http://localhost:4200**

## 📖 Hướng dẫn sử dụng

### Đăng ký nhân viên mới

1. Truy cập **"Thêm nhân viên"**
2. Nhập thông tin (mã NV, họ tên, email...)
3. Click **"Bắt đầu quét khuôn mặt"**
4. Xoay mặt theo vòng tròn (như Face ID)
5. Hệ thống tự động trích xuất nhiều góc độ
6. Click **"Hoàn tất"** → Model tự động train

### Điểm danh

1. Mở **"Điểm danh"**
2. Camera tự động bật
3. Nhìn vào camera
4. Hệ thống tự động nhận diện và ghi log
5. Hiển thị tên + độ chính xác
6. Chỉ điểm danh 1 lần/ngày

### Xem lịch sử

1. Truy cập **"Lịch sử điểm danh"**
2. Xem theo ngày/tuần/tháng
3. Lọc theo nhân viên
4. Export báo cáo

## 🎥 Quy trình hoạt động

### A. Đăng ký (Registration)

```mermaid
graph LR
    A[Bắt đầu] --> B[Quét vòng tròn]
    B --> C[Trích xuất frames]
    C --> D[Phát hiện khuôn mặt]
    D --> E[Extract embeddings]
    E --> F[Augmentation]
    F --> G[Lưu MySQL]
    G --> H[Train SVM]
```

**Chi tiết:**
1. User xoay mặt theo vòng tròn trong 5-10 giây
2. Frontend gửi ~100 frames qua WebSocket
3. Backend xử lý:
   - Phát hiện khuôn mặt (InsightFace)
   - Trích xuất embedding 512-dim
   - Tạo augmented images (xoay, sáng, tối, blur...)
   - Lưu vào MySQL + employee_db.joblib
4. Tự động train lại SVM classifier

### B. Nhận diện (Recognition) - Multiprocessing

```mermaid
graph TB
    A[Camera] --> B[Process 1: Camera + Display]
    B --> C[Queue]
    C --> D[Process 2: AI Recognition]
    D --> E[InsightFace]
    E --> F[SVM Classifier]
    F --> G[Cosine Fallback]
    G --> H[Result Queue]
    H --> B
    F --> I[MySQL: Log Attendance]
```

**Chi tiết:**
- **Process 1** (Main): 
  - Đọc camera 60 FPS
  - Hiển thị video + bounding boxes
  - Gửi frame vào Queue mỗi 1 giây
  
- **Process 2** (AI Worker):
  - Nhận frame từ Queue
  - Phát hiện khuôn mặt → Extract embedding
  - Dự đoán bằng SVM (nếu có model)
  - Fallback: Cosine similarity với database
  - Gửi kết quả về Process 1
  - Log vào MySQL (1 lần/ngày)

## 📊 API Endpoints

### Employees
```http
POST   /api/v1/employees/register/start      # Bắt đầu đăng ký
POST   /api/v1/employees/register/frame/:id  # Upload frame
POST   /api/v1/employees/register/complete   # Hoàn tất
GET    /api/v1/employees                     # Danh sách
GET    /api/v1/employees/:id                 # Chi tiết
PUT    /api/v1/employees/:id                 # Cập nhật
DELETE /api/v1/employees/:id                 # Xóa
```

### Recognition
```http
POST /api/v1/recognition/recognize    # Nhận diện 1 frame
WS   /api/v1/recognition/ws/stream    # WebSocket stream
GET  /api/v1/recognition/camera/info  # Thông tin camera
```

### Attendance
```http
GET /api/v1/attendance/logs           # Lịch sử
GET /api/v1/attendance/today          # Hôm nay
GET /api/v1/attendance/stats          # Thống kê
GET /api/v1/attendance/employee/:id   # Theo nhân viên
```

### System
```http
GET  /api/v1/system/status       # Trạng thái hệ thống
POST /api/v1/system/train-model  # Train lại model
POST /api/v1/system/reload-models # Reload models
```

## ⚙️ Cấu hình

### Backend (.env)
```env
# Database
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/face_recognition_db

# Recognition
RECOGNITION_THRESHOLD=0.5      # Ngưỡng nhận diện (0.4-0.6)
AUGMENTATION_COUNT=5           # Số ảnh augmented/frame
SVM_C=10                       # SVM parameter
SVM_GAMMA=0.1

# Camera
CAMERA_WIDTH=640
CAMERA_HEIGHT=480
PREDICT_INTERVAL=30            # Xử lý AI mỗi 30 frames (1 giây)
```

## 🎯 Performance

| Metric | Value |
|--------|-------|
| Registration Time | 3-5 giây (100 frames) |
| SVM Training | 5-10 giây (50 employees) |
| Recognition Speed | <50ms/frame |
| Display FPS | 60 FPS (multiprocessing) |
| Accuracy | >95% (với đủ training data) |

## 🔧 Troubleshooting

### Camera không hoạt động
```powershell
# Test camera
python -c "import cv2; cap = cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'FAIL')"
```

### MySQL connection error
- Kiểm tra MySQL đang chạy
- Verify credentials trong `.env`
- Test: `mysql -u root -p`

### InsightFace model lỗi
```powershell
# Re-download
python -c "from insightface.app import FaceAnalysis; FaceAnalysis(name='antelopev2').prepare(ctx_id=0)"
```

### Model không nhận diện
- Giảm `RECOGNITION_THRESHOLD` xuống 0.4
- Train lại model: `POST /api/v1/system/train-model`
- Đăng ký lại với nhiều góc độ hơn

## 📚 Documentation

- [Backend README](./backend/README.md)
- [API Documentation](http://localhost:8000/docs)
- [Frontend README](./frontend/README.md) *(coming soon)*

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## 📄 License

MIT License - See LICENSE file

## 👨‍💻 Authors

DACN AI Team - Face Recognition Attendance System

---

## 🎉 Next Steps

✅ **Backend đã hoàn thành!**

🚧 **Frontend Angular đang phát triển...**

Hãy chạy backend và test API tại http://localhost:8000/docs

---

**Made with ❤️ by DACN AI Team**
