# ScheSerAI

Ứng dụng quản lý lịch dạy cho 1 giáo viên (kèm 1-1/nhóm nhỏ): quản lý học viên, lịch học cố định hàng tuần, đồng bộ 2 chiều với Google Calendar, điểm danh, và xuất báo cáo học phí hàng tháng (PDF/PNG).

## Kiến trúc & công nghệ

Dự án gồm 2 phần độc lập, nằm cạnh nhau trong cùng repo:

```
ScheSerAI/
├── backend/    # Django 5 + Django REST Framework (API)
├── frontend/   # Vite + React + TypeScript (giao diện)
├── Docs/       # Tài liệu nghiệp vụ (backlog, database)
└── docker-compose.yml
```

| Phần | Công nghệ |
|---|---|
| Backend | Django 5, Django REST Framework, PostgreSQL, django-q2 (job nền), Google Calendar API |
| Frontend | Vite, React 19, TypeScript, React Router |
| Hạ tầng dev | Docker Compose (Postgres + web + worker) |

## Tính năng chính

- **Học viên** (`apps/students`): tạo/sửa hồ sơ học viên, giá/buổi cố định vĩnh viễn sau khi tạo, tạm nghỉ (deactivate) kèm dọn lịch tương lai.
- **Lịch học & buổi học** (`apps/scheduling`): khai báo lịch cố định hàng tuần → tự sinh trước Session 4-8 tuần; dời lịch / hủy từng buổi riêng lẻ.
- **Đồng bộ Google Calendar** (`apps/teacher`, `apps/scheduling/calendar_sync.py`, `google_sync.py`): đẩy buổi học lên Calendar khi tạo/dời/hủy, đồng thời polling đồng bộ ngược khi giáo viên sửa trực tiếp trên Google Calendar.
- **Điểm danh** (`apps/attendance`): đánh dấu có mặt/vắng, chỉ tính buổi có mặt vào học phí.
- **Học phí** (`apps/billing`): xem trước theo tháng, xuất báo cáo PDF/PNG (pastel theme), lưu lịch sử báo cáo đã xuất.
- **Thông báo** (`apps/notifications`): ghi nhận các thay đổi lịch (dời/hủy/đồng bộ từ Google) để giáo viên không bỏ sót.

## Bắt đầu nhanh

### 1. Backend (Docker Compose — khuyến nghị)

```bash
cp backend/env.example backend/.env
# mở backend/.env, điền GOOGLE_CLIENT_ID/SECRET nếu cần dùng tính năng Google Calendar

docker compose up --build
```

Lần đầu, mở terminal khác để chạy migrate + tạo tài khoản quản trị + đăng ký job nền:

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py bootstrap_scheduled_jobs
```

API chạy tại `http://localhost:8000/api/`, trang quản trị tại `http://localhost:8000/admin/`.

`docker-compose.yml` gồm 3 service: `db` (Postgres), `web` (Django runserver), `worker` (django-q2 cluster chạy job nền — sinh Session hàng tuần + polling Google Calendar).

### 2. Backend (chạy local, không Docker)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp env.example .env
# sửa DATABASE_URL trong .env, ví dụ dùng SQLite cho dev nhanh:
# DATABASE_URL=sqlite:///db.sqlite3

python manage.py migrate
python manage.py createsuperuser
python manage.py bootstrap_scheduled_jobs
python manage.py runserver
```

Chạy job nền (không bắt buộc để dùng API cơ bản, nhưng cần cho tự sinh Session/đồng bộ Google định kỳ):

```bash
python manage.py qcluster
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Mặc định chạy ở `http://localhost:5173`. Hiện frontend đang dùng dữ liệu mẫu (`src/data/mockData.ts`) để dựng giao diện — chưa nối vào API thật của backend.

## Biến môi trường (`backend/.env`)

| Biến | Mô tả |
|---|---|
| `SECRET_KEY` | Khóa bí mật Django |
| `DEBUG` | `True`/`False` |
| `ALLOWED_HOSTS` | Danh sách host, cách nhau bởi dấu phẩy |
| `DATABASE_URL` | Chuỗi kết nối DB (mặc định Postgres qua Docker; có thể đổi sang `sqlite:///db.sqlite3` khi chạy local) |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | OAuth client "Web application" tạo trên Google Cloud Console |
| `GOOGLE_OAUTH_REDIRECT_URI` | Redirect URI đã khai báo trong Google Cloud Console, mặc định `http://localhost:8000/api/google/callback/` |
| `GOOGLE_TOKEN_ENCRYPTION_KEY` | Fernet key mã hóa refresh token khi lưu DB (bỏ trống ở dev sẽ tự suy từ `SECRET_KEY`, production nên đặt riêng) |

Cách lấy `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET`: tạo project trên Google Cloud Console → bật **Google Calendar API** → cấu hình **OAuth consent screen** (scope `calendar.events`, `userinfo.email`) → tạo **OAuth client ID** loại **Web application** với redirect URI khớp `GOOGLE_OAUTH_REDIRECT_URI`.

## API tổng quan

Toàn bộ endpoint nằm dưới `/api/`, xác thực qua session của Django (`/api-auth/`).

| Base path | Mô tả |
|---|---|
| `/api/students/` | CRUD học viên, action `deactivate`, `billing-preview` |
| `/api/schedules/` | Lịch cố định hàng tuần, action `pause`/`resume` |
| `/api/sessions/` | Buổi học, action `mark-attendance`, `bulk-mark-attendance`, `reschedule`, `cancel` |
| `/api/monthly-reports/` | Lịch sử báo cáo học phí, action `preview`, `generate`, `download` |
| `/api/notifications/` | Thông báo, action `unread-count`, `mark-read`, `mark-all-read` |
| `/api/google/connect/`, `/callback/`, `/status/`, `/disconnect/` | Luồng kết nối Google Calendar |

## Chạy test (backend)

```bash
cd backend
python manage.py test apps
```

Nếu chưa có Postgres cục bộ, có thể chạy tạm với SQLite in-memory:

```bash
DATABASE_URL="sqlite:///:memory:" python manage.py test apps
```
