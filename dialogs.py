# dialogs.py (cập nhật: thêm trường ID tùy chọn cho Department/Member/Document)
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton,
    QFileDialog, QSpinBox, QFormLayout, QMessageBox, QComboBox
)
import os

class DepartmentDialog(QDialog):
    def __init__(self, parent=None, department=None):
        super().__init__(parent)
        self.setWindowTitle("Phòng ban" if not department else "Sửa phòng ban")
        self.department = department
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        form = QFormLayout()

        # optional ID input
        self.id_input = QLineEdit(str(self.department['id']) if self.department and self.department.get('id') is not None else '')
        self.id_input.setPlaceholderText("Để trống để tự động sinh/auto")
        form.addRow("ID (tùy chọn):", self.id_input)

        self.name = QLineEdit(self.department['name'] if self.department else '')
        self.desc = QTextEdit(self.department['description'] if self.department else '')
        form.addRow("Tên phòng ban:", self.name)
        form.addRow("Mô tả:", self.desc)
        layout.addLayout(form)
        btns = QHBoxLayout()
        ok = QPushButton("Lưu")
        cancel = QPushButton("Hủy")
        ok.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(ok)
        btns.addWidget(cancel)
        layout.addLayout(btns)
        self.setLayout(layout)

    def get_data(self):
        id_text = self.id_input.text().strip()
        id_val = None
        if id_text != '':
            try:
                id_val = int(id_text)
            except Exception:
                id_val = None
        return {'id': id_val, 'name': self.name.text().strip(), 'description': self.desc.toPlainText().strip()}


class MemberDialog(QDialog):
    def __init__(self, parent=None, member=None, departments=None):
        super().__init__(parent)
        self.setWindowTitle("Thành viên" if not member else "Sửa thành viên")
        self.member = member
        self.departments = departments or []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        form = QFormLayout()

        self.id_input = QLineEdit(str(self.member['id']) if self.member and self.member.get('id') is not None else '')
        self.id_input.setPlaceholderText("Để trống để tự động sinh/auto")
        form.addRow("ID (tùy chọn):", self.id_input)

        self.full_name = QLineEdit(self.member['full_name'] if self.member else '')
        self.position = QLineEdit(self.member.get('position','') if self.member else '')
        self.email = QLineEdit(self.member.get('email','') if self.member else '')
        self.phone = QLineEdit(self.member.get('phone','') if self.member else '')
        self.notes = QTextEdit(self.member.get('notes','') if self.member else '')

        self.dept_combo = QComboBox()
        for d in self.departments:
            self.dept_combo.addItem(d['name'], d['id'])
        if self.member:
            idx = 0
            for i in range(self.dept_combo.count()):
                if self.dept_combo.itemData(i) == self.member.get('department_id'):
                    idx = i; break
            self.dept_combo.setCurrentIndex(idx)

        form.addRow("Tên đầy đủ:", self.full_name)
        form.addRow("Chức vụ:", self.position)
        form.addRow("Email:", self.email)
        form.addRow("Số điện thoại:", self.phone)
        form.addRow("Thuộc phòng ban:", self.dept_combo)
        form.addRow("Ghi chú:", self.notes)
        layout.addLayout(form)
        btns = QHBoxLayout()
        ok = QPushButton("Lưu")
        cancel = QPushButton("Hủy")
        ok.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(ok)
        btns.addWidget(cancel)
        layout.addLayout(btns)
        self.setLayout(layout)

    def get_data(self):
        id_text = self.id_input.text().strip()
        id_val = None
        if id_text != '':
            try:
                id_val = int(id_text)
            except Exception:
                id_val = None
        dept_id = self.dept_combo.currentData()
        return {
            'id': id_val,
            'full_name': self.full_name.text().strip(),
            'position': self.position.text().strip(),
            'email': self.email.text().strip(),
            'phone': self.phone.text().strip(),
            'notes': self.notes.toPlainText().strip(),
            'department_id': dept_id
        }


class DocumentDialog(QDialog):
    def __init__(self, parent=None, document=None):
        super().__init__(parent)
        self.setWindowTitle("Hồ sơ / Tài liệu" if not document else "Sửa hồ sơ")
        self.document = document
        self.file_src = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        form = QFormLayout()

        self.id_input = QLineEdit(str(self.document['id']) if self.document and self.document.get('id') is not None else '')
        self.id_input.setPlaceholderText("Để trống để tự động sinh/auto")
        form.addRow("ID (tùy chọn):", self.id_input)

        self.tt = QSpinBox()
        self.tt.setMinimum(0)
        self.tt.setMaximum(9999)
        if self.document and self.document.get('tt') is not None:
            self.tt.setValue(int(self.document.get('tt')))

        self.so_ky_hieu = QLineEdit(self.document.get('so_ky_hieu','') if self.document else '')
        self.ngay_thang = QLineEdit(self.document.get('ngay_thang','') if self.document else '')
        self.ten_loai = QLineEdit(self.document.get('ten_loai_trichyeu','') if self.document else '')
        self.tac_gia = QLineEdit(self.document.get('tac_gia','') if self.document else '')
        self.so_to = QLineEdit(self.document.get('so_to','') if self.document else '')
        self.ghi_chu = QTextEdit(self.document.get('ghi_chu','') if self.document else '')
        self.file_label = QLabel(self.document.get('file_path','(chưa có)') if self.document else '(chưa có)')
        btn_select = QPushButton("Chọn file PDF...")
        btn_select.clicked.connect(self.on_select_file)
        form.addRow("TT:", self.tt)
        form.addRow("Số và Ký hiệu:", self.so_ky_hieu)
        form.addRow("Ngày tháng:", self.ngay_thang)
        form.addRow("Tên loại & trích yếu:", self.ten_loai)
        form.addRow("Tác giả:", self.tac_gia)
        form.addRow("Số tờ (bản):", self.so_to)
        form.addRow("Ghi chú:", self.ghi_chu)
        h = QHBoxLayout()
        h.addWidget(self.file_label)
        h.addWidget(btn_select)
        form.addRow("Link hồ sơ (file):", h)
        layout.addLayout(form)
        btns = QHBoxLayout()
        ok = QPushButton("Lưu")
        cancel = QPushButton("Hủy")
        ok.clicked.connect(self._on_ok)
        cancel.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(ok)
        btns.addWidget(cancel)
        layout.addLayout(btns)
        self.setLayout(layout)

    def on_select_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Chọn file PDF", "", "PDF Files (*.pdf)")
        if path:
            self.file_src = path
            self.file_label.setText(os.path.basename(path))

    def _on_ok(self):
        if not self.ten_loai.text().strip():
            QMessageBox.warning(self, "Thiếu", "Vui lòng nhập 'Tên loại & trích yếu nội dung'")
            return
        self.accept()

    def get_data(self):
        id_text = self.id_input.text().strip()
        id_val = None
        if id_text != '':
            try:
                id_val = int(id_text)
            except Exception:
                id_val = None
        return {
            'id': id_val,
            'tt': self.tt.value(),
            'so_ky_hieu': self.so_ky_hieu.text().strip(),
            'ngay_thang': self.ngay_thang.text().strip(),
            'ten_loai_trichyeu': self.ten_loai.text().strip(),
            'tac_gia': self.tac_gia.text().strip(),
            'so_to': self.so_to.text().strip(),
            'ghi_chu': self.ghi_chu.toPlainText().strip(),
            'file_src': self.file_src
        }