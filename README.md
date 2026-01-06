# Ứng dụng Quản lý Phòng ban & Thành viên (Desktop, Python + PySide6)

Mô tả
- Ứng dụng desktop (chạy offline nội bộ).
- CRUD Phòng ban (Departments).
- CRUD Thành viên (Members) thuộc từng phòng ban.
- Mỗi thành viên có thể có nhiều hồ sơ/tài liệu (Documents) theo format:
  TT, Số và Ký hiệu, Ngày tháng, Tên loại & trích yếu nội dung, Tác giả, Số tờ (bản), Ghi chú, Link hồ sơ (file PDF).
- Lưu trữ lâu dài: SQLite DB tại `./data/database.sqlite`, PDF được copy vào `./data/uploads`.
- Có chức năng export (tạo zip chứa database + uploads) để bàn giao.
- Mở file PDF bằng ứng dụng mặc định trên hệ điều hành.

Yêu cầu
- Python 3.10+ (hoặc 3.8+)
- pip install -r requirements.txt

Cài đặt & chạy nhanh
1. Tạo virtualenv (tùy chọn)
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows

2. Cài dependencies
   pip install -r requirements.txt

3. Chạy ứng dụng
   python main.py

Packaging (tạo file .exe / .app)
- Sử dụng PyInstaller:
  pip install pyinstaller
  pyinstaller --onefile --add-data "data:./data" main.py
  Hoặc sử dụng spec file để include thư mục data/uploads nếu muốn.

Đóng gói để bàn giao
- Chạy Export trong menu (File -> Export data...) để tạo một file zip chứa:
  - database.sqlite
  - uploads/*

Vị trí lưu dữ liệu
- Database: ./data/database.sqlite
- Uploads: ./data/uploads/

Gợi ý bảo mật / mở rộng
- Thêm quyền truy cập/role nếu cần (auth).
- Tự động backup DB hàng ngày.
- Nếu muốn multi-user trong mạng nội bộ, cân nhắc chuyển sang server DB (Postgres) + client app.

Nếu bạn muốn, tôi sẽ:
- Tạo sẵn file exe bằng PyInstaller cho Windows.
- Thêm tính năng tìm kiếm nâng cao / in PDF / xuất CSV.