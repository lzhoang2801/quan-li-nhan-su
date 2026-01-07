import sqlite3
import os
import shutil
from datetime import datetime
from openpyxl import Workbook, load_workbook
from openpyxl.utils import get_column_letter

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
UPLOADS_DIR = os.path.join(DATA_DIR, 'uploads')
DB_PATH = os.path.join(DATA_DIR, 'database.sqlite')

os.makedirs(UPLOADS_DIR, exist_ok=True)

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS departments (
      id INTEGER PRIMARY KEY,
      name TEXT NOT NULL UNIQUE,
      description TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS members (
      id INTEGER PRIMARY KEY,
      department_id INTEGER NOT NULL,
      full_name TEXT NOT NULL,
      position TEXT,
      email TEXT,
      phone TEXT,
      notes TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY(department_id) REFERENCES departments(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS documents (
      id INTEGER PRIMARY KEY,
      member_id INTEGER NOT NULL,
      tt INTEGER,
      so_ky_hieu TEXT,
      ngay_thang TEXT,
      ten_loai_trichyeu TEXT,
      tac_gia TEXT,
      so_to TEXT,
      ghi_chu TEXT,
      file_path TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY(member_id) REFERENCES members(id) ON DELETE CASCADE
    );
    """)
    conn.commit()
    conn.close()

# ---------------- Departments ----------------
def list_departments():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM departments ORDER BY created_at DESC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def create_department(name, description='', id_=None):
    conn = get_conn()
    cur = conn.cursor()
    if id_:
        cur.execute("INSERT INTO departments (id, name, description) VALUES (?, ?, ?)", (id_, name, description))
        new_id = id_
    else:
        cur.execute("INSERT INTO departments (name, description) VALUES (?, ?)", (name, description))
        new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return new_id

def update_department(id_, name, description):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE departments SET name=?, description=? WHERE id=?", (name, description, id_))
    conn.commit()
    conn.close()

def delete_department(id_, remove_files=False):
    """
    Xóa phòng ban và các thành viên + hồ sơ liên quan.
    Nếu remove_files=True -> xóa cả file trên disk (uploads) của những hồ sơ này.
    """
    conn = get_conn()
    cur = conn.cursor()
    # Lấy các member thuộc dept
    cur.execute("SELECT id FROM members WHERE department_id = ?", (id_,))
    member_rows = cur.fetchall()
    member_ids = [r['id'] for r in member_rows]
    if remove_files:
        for mid in member_ids:
            docs = list_documents_by_member(mid)
            for d in docs:
                fp = d.get('file_path')
                if fp and os.path.exists(fp):
                    try:
                        os.remove(fp)
                    except Exception:
                        pass
    # Xóa members (documents bị cascade)
    cur.execute("DELETE FROM members WHERE department_id = ?", (id_,))
    # Xóa department
    cur.execute("DELETE FROM departments WHERE id = ?", (id_,))
    conn.commit()
    conn.close()

# ---------------- Members ----------------
def list_members_by_dept(dept_id, order_by='m.created_at DESC'):
    """
    Lấy members của dept_id. order_by phải là chuỗi SQL hợp lệ cho phần ORDER BY
    (ví dụ: 'm.id ASC', 'm.full_name COLLATE NOCASE ASC', 'm.created_at DESC').
    Trong UI chúng ta chỉ truyền các giá trị định trước.
    """
    conn = get_conn()
    cur = conn.cursor()
    sql = f"SELECT m.*, d.name as department_name FROM members m JOIN departments d ON m.department_id=d.id WHERE department_id=? ORDER BY {order_by}"
    cur.execute(sql, (dept_id,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def list_all_members(order_by='m.created_at DESC'):
    conn = get_conn()
    cur = conn.cursor()
    sql = f"SELECT m.*, d.name as department_name FROM members m JOIN departments d ON m.department_id=d.id ORDER BY {order_by}"
    cur.execute(sql)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def get_member(id_):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM members WHERE id=?", (id_,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def create_member(dept_id, full_name, position='', email='', phone='', notes='', id_=None):
    conn = get_conn()
    cur = conn.cursor()
    if id_:
        cur.execute("INSERT INTO members (id, department_id, full_name, position, email, phone, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (id_, dept_id, full_name, position, email, phone, notes))
        new_id = id_
    else:
        cur.execute("INSERT INTO members (department_id, full_name, position, email, phone, notes) VALUES (?, ?, ?, ?, ?, ?)",
                    (dept_id, full_name, position, email, phone, notes))
        new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return new_id

def update_member(id_, full_name, position, email, phone, notes, department_id=None):
    conn = get_conn()
    cur = conn.cursor()
    if department_id:
        cur.execute("""UPDATE members SET full_name=?, position=?, email=?, phone=?, notes=?, department_id=? WHERE id=?""",
                    (full_name, position, email, phone, notes, department_id, id_))
    else:
        cur.execute("""UPDATE members SET full_name=?, position=?, email=?, phone=?, notes=? WHERE id=?""",
                    (full_name, position, email, phone, notes, id_))
    conn.commit()
    conn.close()

def delete_member(id_):
    # delete documents files first
    docs = list_documents_by_member(id_)
    for d in docs:
        if d.get('file_path') and os.path.exists(d['file_path']):
            try:
                os.remove(d['file_path'])
            except Exception:
                pass
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM members WHERE id=?", (id_,))
    conn.commit()
    conn.close()

def change_member_id(old_id, new_id):
    """
    Thay id của member từ old_id -> new_id an toàn (transaction).
    """
    if old_id == new_id:
        return
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM members WHERE id = ?", (old_id,))
        old = cur.fetchone()
        if not old:
            raise ValueError(f"Member id {old_id} không tồn tại")
        cur.execute("SELECT 1 FROM members WHERE id = ?", (new_id,))
        if cur.fetchone():
            raise ValueError(f"Member id {new_id} đã tồn tại")
        conn.execute("BEGIN")
        department_id = old["department_id"]
        full_name = old["full_name"]
        position = old["position"]
        email = old["email"]
        phone = old["phone"]
        notes = old["notes"]
        created_at = old["created_at"]
        cur.execute("""
            INSERT INTO members (id, department_id, full_name, position, email, phone, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (new_id, department_id, full_name, position, email, phone, notes, created_at))
        cur.execute("UPDATE documents SET member_id = ? WHERE member_id = ?", (new_id, old_id))
        cur.execute("DELETE FROM members WHERE id = ?", (old_id,))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

# ---------------- Documents ----------------
def list_documents_by_member(member_id, order_by='tt ASC, created_at DESC'):
    """
    Lấy documents của member_id; order_by là chuỗi SQL hợp lệ cho ORDER BY.
    """
    conn = get_conn()
    cur = conn.cursor()
    sql = f"SELECT * FROM documents WHERE member_id=? ORDER BY {order_by}"
    cur.execute(sql, (member_id,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def get_document(id_):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM documents WHERE id=?", (id_,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def _copy_file_to_uploads(src_path):
    if not src_path:
        return None
    if not os.path.exists(src_path):
        return None
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    filename = f"{int(datetime.now().timestamp())}_{os.path.basename(src_path).replace(' ', '_')}"
    dest = os.path.join(UPLOADS_DIR, filename)
    shutil.copy2(src_path, dest)
    return dest

def create_document(member_id, tt=None, so_ky_hieu='', ngay_thang='', ten_loai_trichyeu='',
                    tac_gia='', so_to='', ghi_chu='', file_src_path=None, id_=None):
    file_path = _copy_file_to_uploads(file_src_path) if file_src_path else None
    conn = get_conn()
    cur = conn.cursor()
    if id_:
        cur.execute("""
        INSERT INTO documents (id, member_id, tt, so_ky_hieu, ngay_thang, ten_loai_trichyeu, tac_gia, so_to, ghi_chu, file_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (id_, member_id, tt, so_ky_hieu, ngay_thang, ten_loai_trichyeu, tac_gia, so_to, ghi_chu, file_path))
        new_id = id_
    else:
        cur.execute("""
        INSERT INTO documents (member_id, tt, so_ky_hieu, ngay_thang, ten_loai_trichyeu, tac_gia, so_to, ghi_chu, file_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (member_id, tt, so_ky_hieu, ngay_thang, ten_loai_trichyeu, tac_gia, so_to, ghi_chu, file_path))
        new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return new_id

def update_document(id_, tt=None, so_ky_hieu='', ngay_thang='', ten_loai_trichyeu='',
                    tac_gia='', so_to='', ghi_chu='', file_src_path=None):
    existing = get_document(id_)
    file_path = existing.get('file_path') if existing else None
    if file_src_path:
        new_path = _copy_file_to_uploads(file_src_path)
        if new_path:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass
            file_path = new_path
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
      UPDATE documents SET tt=?, so_ky_hieu=?, ngay_thang=?, ten_loai_trichyeu=?, tac_gia=?, so_to=?, ghi_chu=?, file_path=?
      WHERE id=?
    """, (tt, so_ky_hieu, ngay_thang, ten_loai_trichyeu, tac_gia, so_to, ghi_chu, file_path, id_))
    conn.commit()
    conn.close()

def delete_document(id_):
    doc = get_document(id_)
    if doc and doc.get('file_path') and os.path.exists(doc['file_path']):
        try:
            os.remove(doc['file_path'])
        except Exception:
            pass
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM documents WHERE id=?", (id_,))
    conn.commit()
    conn.close()

# ---------------- Export ZIP ----------------
def export_data_zip(dest_zip_path):
    import zipfile
    with zipfile.ZipFile(dest_zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        if os.path.exists(DB_PATH):
            z.write(DB_PATH, arcname='database.sqlite')
        for root, dirs, files in os.walk(UPLOADS_DIR):
            for f in files:
                full = os.path.join(root, f)
                arc = os.path.relpath(full, DATA_DIR)
                z.write(full, arcname=os.path.join('uploads', arc))

# ---------------- Search ----------------
def search_members(name_contains=None, position_contains=None, department_id=None, has_docs=None, order_by='m.created_at DESC'):
    conn = get_conn()
    cur = conn.cursor()
    clauses = []
    params = []

    base = "SELECT m.*, d.name as department_name FROM members m JOIN departments d ON m.department_id = d.id"

    if has_docs is True:
        base += " WHERE EXISTS (SELECT 1 FROM documents doc WHERE doc.member_id = m.id)"
    elif has_docs is False:
        base += " WHERE NOT EXISTS (SELECT 1 FROM documents doc WHERE doc.member_id = m.id)"
    else:
        base += " WHERE 1=1"

    if name_contains:
        clauses.append("m.full_name LIKE ?")
        params.append(f"%{name_contains}%")
    if position_contains:
        clauses.append("m.position LIKE ?")
        params.append(f"%{position_contains}%")
    if department_id:
        clauses.append("m.department_id = ?")
        params.append(department_id)

    if clauses:
        base += " AND " + " AND ".join(clauses)

    base += f" ORDER BY {order_by}"

    cur.execute(base, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

# ---------------- Excel Export / Import / Reset ----------------
# (giữ nguyên các hàm export_to_excel, import_from_excel, clear_database, reset_database từ phiên bản trước)
# ... (nếu cần, bạn vẫn có các hàm đó trong file hiện tại) ...