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
- Windows (recommended - ship data next to exe):
  1) Cài PyInstaller: pip install pyinstaller
  2) Build (onedir, giữ thư mục data để DB/uploads có thể ghi được):
     pyinstaller --noconfirm --onedir --windowed --add-data "data;data" --name DeptMemberManager main.py
  - One-file alternative: --onefile tạo EXE từng file nhưng thư mục data sẽ được giải nén vào thư mục tạm khi chạy và các thay đổi (DB/uploads) có thể không được giữ lại; nếu cần dữ liệu bền vững, dùng --onedir hoặc thay đổi `db.py` để lưu dữ liệu vào %APPDATA%.
  - Khi build xong, tìm file dưới: dist\DeptMemberManager\ (onedir) hoặc dist\DeptMemberManager.exe (onefile)

  Tip: Nếu muốn EXE ghi dữ liệu bền vững khi dùng --onefile, thay đổi `db.py` để dùng thư mục người dùng (ví dụ %APPDATA%). Ví dụ nhanh:

  ```python
  import sys, os
  if getattr(sys, 'frozen', False):
      base = os.path.join(os.getenv('APPDATA') or os.path.expanduser('~'), 'DeptMemberManager')
  else:
      base = os.path.abspath(os.path.dirname(__file__))
  DATA_DIR = os.path.join(base, 'data')
  os.makedirs(DATA_DIR, exist_ok=True)
  ```

  Hoặc dùng `--onedir` để đơn giản (thư mục `data` được đóng gói sát bên exe và có thể sửa đổi).

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