import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QPushButton, QLabel, QSplitter, QTableWidget, QTableWidgetItem, QAbstractItemView,
    QMessageBox, QFileDialog, QLineEdit, QComboBox, QDialog
)
from PySide6.QtGui import QAction as GuiAction
from PySide6.QtCore import Qt, QSize
import db
from dialogs import DepartmentDialog, MemberDialog, DocumentDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Quản lý Phòng ban & Thành viên")
        self.resize(1100, 700)
        self._build_ui()
        self.refresh_departments()

    def _build_ui(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        export_excel_act = GuiAction("Export Excel...", self)
        export_excel_act.triggered.connect(self.on_export_excel)
        file_menu.addAction(export_excel_act)
        export_zip_act = GuiAction("Export dữ liệu (zip)", self)
        export_zip_act.triggered.connect(self.on_export)
        file_menu.addAction(export_zip_act)
        import_act = GuiAction("Import từ Excel...", self)
        import_act.triggered.connect(self.on_import_excel)
        file_menu.addAction(import_act)
        reset_act = GuiAction("Reset DB (clear)", self)
        reset_act.triggered.connect(self.on_reset_db)
        file_menu.addAction(reset_act)
        file_menu.addSeparator()
        exit_act = GuiAction("Thoát", self)
        exit_act.triggered.connect(self.close)
        file_menu.addAction(exit_act)

        actions_menu = menubar.addMenu("Hành động")
        add_dept_act = GuiAction("Thêm phòng ban", self)
        add_dept_act.triggered.connect(self.on_add_department)
        add_member_act = GuiAction("Thêm thành viên", self)
        add_member_act.triggered.connect(self.on_add_member)
        actions_menu.addAction(add_dept_act)
        actions_menu.addAction(add_member_act)

        help_menu = menubar.addMenu("Trợ giúp")
        about_act = GuiAction("Giới thiệu", self)
        about_act.triggered.connect(self.on_about)
        help_menu.addAction(about_act)

        central = QWidget()
        central_layout = QVBoxLayout()
        central.setLayout(central_layout)

        # Search bar
        search_bar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Tìm theo tên (Enter để tìm)...")
        self.search_input.returnPressed.connect(self.on_search)

        self.filter_dept = QComboBox()
        self.filter_dept.addItem("Tất cả phòng ban", None)

        self.filter_position = QLineEdit()
        self.filter_position.setPlaceholderText("Lọc chức vụ...")

        self.filter_has_docs = QComboBox()
        self.filter_has_docs.addItem("Tất cả", None)
        self.filter_has_docs.addItem("Có hồ sơ", True)
        self.filter_has_docs.addItem("Chưa có hồ sơ", False)

        btn_search = QPushButton("Tìm")
        btn_search.clicked.connect(self.on_search)
        btn_clear = QPushButton("Xóa")
        btn_clear.clicked.connect(self.on_clear_search)

        search_bar.addWidget(QLabel("Tìm:"))
        search_bar.addWidget(self.search_input)
        search_bar.addWidget(QLabel("Phòng ban:"))
        search_bar.addWidget(self.filter_dept)
        search_bar.addWidget(QLabel("Chức vụ:"))
        search_bar.addWidget(self.filter_position)
        search_bar.addWidget(self.filter_has_docs)
        search_bar.addWidget(btn_search)
        search_bar.addWidget(btn_clear)
        central_layout.addLayout(search_bar)

        splitter = QSplitter(Qt.Horizontal)

        # Left: departments
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)
        left_layout.addWidget(QLabel("<b>Phòng ban</b>"))
        self.list_depts = QListWidget()
        self.list_depts.itemClicked.connect(self.on_dept_selected)
        left_layout.addWidget(self.list_depts)
        left_btns = QHBoxLayout()
        btn_refresh_dept = QPushButton("Tải lại")
        btn_refresh_dept.clicked.connect(self.refresh_departments)
        btn_delete_dept = QPushButton("Xóa")
        btn_delete_dept.clicked.connect(self.on_delete_department)
        left_btns.addWidget(btn_refresh_dept)
        left_btns.addWidget(btn_delete_dept)
        left_layout.addLayout(left_btns)

        # Middle: members + sort control
        mid_widget = QWidget()
        mid_layout = QVBoxLayout()
        mid_widget.setLayout(mid_layout)
        mid_header = QHBoxLayout()
        mid_header.addWidget(QLabel("<b>Thành viên</b>"))
        # Sort combobox for members
        self.members_sort = QComboBox()
        self.members_sort.addItem("Mặc định (Ngày tạo ↓)", "m.created_at DESC")
        self.members_sort.addItem("ID ↑", "m.id ASC")
        self.members_sort.addItem("ID ↓", "m.id DESC")
        self.members_sort.addItem("Tên A-Z", "m.full_name COLLATE NOCASE ASC")
        self.members_sort.addItem("Tên Z-A", "m.full_name COLLATE NOCASE DESC")
        self.members_sort.addItem("Ngày tạo ↑", "m.created_at ASC")
        self.members_sort.addItem("Ngày tạo ↓", "m.created_at DESC")
        self.members_sort.currentIndexChanged.connect(self.on_members_sort_changed)
        mid_header.addStretch()
        mid_header.addWidget(QLabel("Sắp xếp:"))
        mid_header.addWidget(self.members_sort)
        # compact action buttons
        btn_edit_member = QPushButton("Sửa")
        btn_edit_member.clicked.connect(self.on_edit_member)
        btn_del_member = QPushButton("Xóa")
        btn_del_member.clicked.connect(self.on_delete_member)
        mid_header.addWidget(btn_edit_member)
        mid_header.addWidget(btn_del_member)
        mid_layout.addLayout(mid_header)

        self.table_members = QTableWidget(0, 4)
        self.table_members.setHorizontalHeaderLabels(["ID", "Họ & tên", "Chức vụ", "Phòng ban"])
        self.table_members.verticalHeader().setVisible(False)
        self.table_members.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_members.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_members.cellDoubleClicked.connect(self.on_member_double)
        mid_layout.addWidget(self.table_members)

        # Right: details & documents + sort control
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_widget.setLayout(right_layout)
        right_layout.addWidget(QLabel("<b>Chi tiết & Hồ sơ</b>"))
        self.lbl_member_info = QLabel("(Chọn thành viên để xem chi tiết)")
        self.lbl_member_info.setWordWrap(True)
        right_layout.addWidget(self.lbl_member_info)

        # docs sort combobox
        docs_top = QHBoxLayout()
        docs_top.addStretch()
        docs_top.addWidget(QLabel("Sắp xếp hồ sơ:"))
        self.docs_sort = QComboBox()
        # default by TT then created_at desc
        self.docs_sort.addItem("TT ↑", "tt ASC, created_at DESC")
        self.docs_sort.addItem("TT ↓", "tt DESC, created_at DESC")
        self.docs_sort.addItem("ID ↑", "id ASC")
        self.docs_sort.addItem("ID ↓", "id DESC")
        self.docs_sort.addItem("Ngày tạo ↑", "created_at ASC")
        self.docs_sort.addItem("Ngày tạo ↓", "created_at DESC")
        self.docs_sort.currentIndexChanged.connect(self.on_docs_sort_changed)
        docs_top.addWidget(self.docs_sort)
        right_layout.addLayout(docs_top)

        self.table_docs = QTableWidget(0, 8)
        self.table_docs.setHorizontalHeaderLabels(["TT","Số & Ký hiệu","Ngày tháng","Tên loại & trích yếu","Tác giả","Số tờ","Ghi chú","File"])
        self.table_docs.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_docs.setEditTriggers(QAbstractItemView.NoEditTriggers)
        right_layout.addWidget(self.table_docs)

        docs_btns = QHBoxLayout()
        self.btn_add_doc = QPushButton("Thêm")
        self.btn_add_doc.clicked.connect(self.on_add_document)
        self.btn_edit_doc = QPushButton("Sửa")
        self.btn_edit_doc.clicked.connect(self.on_edit_document)
        self.btn_del_doc = QPushButton("Xóa")
        self.btn_del_doc.clicked.connect(self.on_delete_document)
        self.btn_open_doc = QPushButton("Mở file")
        self.btn_open_doc.clicked.connect(self.on_open_document)
        docs_btns.addWidget(self.btn_add_doc)
        docs_btns.addWidget(self.btn_edit_doc)
        docs_btns.addWidget(self.btn_del_doc)
        docs_btns.addWidget(self.btn_open_doc)
        right_layout.addLayout(docs_btns)

        splitter.addWidget(left_widget)
        splitter.addWidget(mid_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([180, 380, 520])

        central_layout.addWidget(splitter)
        self.setCentralWidget(central)

    # Departments
    def refresh_departments(self):
        self.list_depts.clear()
        self.depts = db.list_departments()
        self.filter_dept.blockSignals(True)
        self.filter_dept.clear()
        self.filter_dept.addItem("Tất cả phòng ban", None)
        for d in self.depts:
            self.filter_dept.addItem(d['name'], d['id'])
            self.list_depts.addItem(d['name'])
        self.filter_dept.blockSignals(False)
        self.clear_member_views()

    def clear_member_views(self):
        self.table_members.setRowCount(0)
        self.table_docs.setRowCount(0)
        self.lbl_member_info.setText("(Chọn thành viên để xem chi tiết)")

    def get_selected_dept(self):
        idx = self.list_depts.currentRow()
        if idx < 0 or idx >= len(self.depts):
            return None
        return self.depts[idx]

    def on_dept_selected(self, item):
        dept = self.get_selected_dept()
        if dept:
            # load members with current sort
            order_by = self.members_sort.currentData() or "m.created_at DESC"
            self.load_members_for_dept(dept['id'], order_by=order_by)

    # Members
    def load_members_for_dept(self, dept_id, order_by=None):
        order_by = order_by or (self.members_sort.currentData() or "m.created_at DESC")
        members = db.list_members_by_dept(dept_id, order_by=order_by)
        self.show_members_in_table(members)

    def show_members_in_table(self, members):
        self.members = members
        self.table_members.setRowCount(0)
        for r, m in enumerate(members):
            self.table_members.insertRow(r)
            self.table_members.setItem(r, 0, QTableWidgetItem(str(m['id'])))
            self.table_members.setItem(r, 1, QTableWidgetItem(m['full_name']))
            self.table_members.setItem(r, 2, QTableWidgetItem(m.get('position','')))
            dept_name = m.get('department_name') or next((d['name'] for d in self.depts if d['id'] == m['department_id']), '')
            self.table_members.setItem(r, 3, QTableWidgetItem(dept_name))
        self.table_docs.setRowCount(0)
        self.lbl_member_info.setText("(Chọn thành viên để xem chi tiết)")

    def on_members_sort_changed(self, idx):
        # reload members for current selected department or search results
        dept = self.get_selected_dept()
        if dept:
            order_by = self.members_sort.itemData(idx)
            self.load_members_for_dept(dept['id'], order_by=order_by)
        else:
            # if showing search results, re-run search with order_by
            self.on_search()

    # CRUD create with optional IDs (unchanged)
    def on_add_department(self):
        dlg = DepartmentDialog(self)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            if not data['name']:
                QMessageBox.warning(self, "Thiếu", "Tên phòng ban yêu cầu")
                return
            try:
                db.create_department(data['name'], data['description'], id_=data.get('id'))
                self.refresh_departments()
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", str(e))

    def on_edit_department(self):
        dept = self.get_selected_dept()
        if not dept:
            QMessageBox.information(self, "Chọn", "Chọn phòng ban để sửa")
            return
        dlg = DepartmentDialog(self, department=dept)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            try:
                db.update_department(dept['id'], data['name'], data['description'])
                self.refresh_departments()
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", str(e))

    def on_delete_department(self):
        dept = self.get_selected_dept()
        if not dept:
            QMessageBox.information(self, "Chọn", "Vui lòng chọn phòng ban để xóa")
            return
        ok = QMessageBox.question(self, "Xác nhận", f"Bạn có chắc muốn xóa phòng ban '{dept['name']}' cùng toàn bộ thành viên và hồ sơ thuộc phòng ban này?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if ok != QMessageBox.StandardButton.Yes:
            return
        rm = QMessageBox.question(self, "Xóa files", "Bạn có muốn xóa cả file hồ sơ (PDF) trên ổ đĩa không? (Yes = xóa file, No = giữ file)", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        remove_files = (rm == QMessageBox.StandardButton.Yes)
        try:
            db.delete_department(dept['id'], remove_files=remove_files)
            QMessageBox.information(self, "Hoàn tất", f"Đã xóa phòng ban '{dept['name']}'")
            self.refresh_departments()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", str(e))

    # Member edit with ID change handled (unchanged from previous)
    def on_add_member(self):
        depts = db.list_departments()
        if not depts:
            QMessageBox.information(self, "Không có phòng ban", "Vui lòng tạo phòng ban trước")
            return
        dlg = MemberDialog(self, member=None, departments=depts)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            if not data['full_name']:
                QMessageBox.warning(self, "Thiếu", "Tên thành viên yêu cầu")
                return
            try:
                db.create_member(data['department_id'], data['full_name'], data['position'], data['email'], data['phone'], data['notes'], id_=data.get('id'))
                cur_dept = self.get_selected_dept()
                if cur_dept and cur_dept['id'] == data['department_id']:
                    self.load_members_for_dept(cur_dept['id'])
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", str(e))

    def get_selected_member(self):
        sel = self.table_members.selectedItems()
        if not sel:
            return None
        row = sel[0].row()
        member_id = int(self.table_members.item(row, 0).text())
        for m in getattr(self, 'members', []):
            if m['id'] == member_id:
                return m
        return None

    def on_edit_member(self):
        m = self.get_selected_member()
        if not m:
            QMessageBox.information(self, "Chọn", "Chọn thành viên để sửa")
            return
        depts = db.list_departments()
        dlg = MemberDialog(self, member=m, departments=depts)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            if not data['full_name']:
                QMessageBox.warning(self, "Thiếu", "Tên thành viên yêu cầu")
                return
            try:
                new_id = data.get('id')
                old_id = m['id']
                if new_id is not None and new_id != old_id:
                    reply = QMessageBox.question(self, "Xác nhận đổi ID",
                        f"Bạn muốn đổi ID của thành viên '{m['full_name']}' từ {old_id} sang {new_id}?\n(Thao tác sẽ cập nhật tất cả hồ sơ liên quan)",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                    if reply != QMessageBox.StandardButton.Yes:
                        return
                    db.change_member_id(old_id, new_id)
                    target_id = new_id
                else:
                    target_id = old_id
                db.update_member(target_id, data['full_name'], data['position'], data['email'], data['phone'], data['notes'], department_id=data['department_id'])
                cur_dept = self.get_selected_dept()
                if cur_dept:
                    self.load_members_for_dept(cur_dept['id'])
                else:
                    self.on_search()
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", str(e))

    def on_delete_member(self):
        m = self.get_selected_member()
        if not m:
            QMessageBox.information(self, "Chọn", "Chọn thành viên để xóa")
            return
        if QMessageBox.question(self, "Xác nhận", f"Xóa thành viên '{m['full_name']}'?") == QMessageBox.StandardButton.Yes:
            db.delete_member(m['id'])
            cur_dept = self.get_selected_dept()
            if cur_dept:
                self.load_members_for_dept(cur_dept['id'])
            else:
                self.on_search()

    def on_member_double(self, row, col):
        try:
            member_id = int(self.table_members.item(row, 0).text())
        except Exception:
            return
        for m in getattr(self, 'members', []):
            if m['id'] == member_id:
                self.show_member_details(m)
                break

    def show_member_details(self, m):
        self.lbl_member_info.setText(f"<b>{m['full_name']}</b><br/>Chức vụ: {m.get('position','')}<br/>Email: {m.get('email','')}<br/>Phone: {m.get('phone','')}<br/>Ghi chú: {m.get('notes','')}")
        order_by = self.docs_sort.currentData() or 'tt ASC, created_at DESC'
        docs = db.list_documents_by_member(m['id'], order_by=order_by)
        self.current_docs = docs
        self.table_docs.setRowCount(0)
        for r, d in enumerate(docs):
            self.table_docs.insertRow(r)
            self.table_docs.setItem(r, 0, QTableWidgetItem(str(d.get('tt') or '')))
            self.table_docs.setItem(r, 1, QTableWidgetItem(d.get('so_ky_hieu','')))
            self.table_docs.setItem(r, 2, QTableWidgetItem(d.get('ngay_thang','')))
            self.table_docs.setItem(r, 3, QTableWidgetItem(d.get('ten_loai_trichyeu','')))
            self.table_docs.setItem(r, 4, QTableWidgetItem(d.get('tac_gia','')))
            self.table_docs.setItem(r, 5, QTableWidgetItem(d.get('so_to','')))
            self.table_docs.setItem(r, 6, QTableWidgetItem(d.get('ghi_chu','')))
            fp = d.get('file_path') or ''
            self.table_docs.setItem(r, 7, QTableWidgetItem(os.path.basename(fp) if fp else ''))

    # Documents handlers (unchanged)
    def get_selected_doc(self):
        sel = self.table_docs.selectedItems()
        if not sel:
            return None
        row = sel[0].row()
        if hasattr(self, 'current_docs') and row < len(self.current_docs):
            return self.current_docs[row]
        return None

    def on_add_document(self):
        m = self.get_selected_member()
        if not m:
            QMessageBox.information(self, "Chọn", "Chọn thành viên để thêm hồ sơ")
            return
        dlg = DocumentDialog(self)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            try:
                db.create_document(m['id'], tt=data['tt'], so_ky_hieu=data['so_ky_hieu'], ngay_thang=data['ngay_thang'],
                                   ten_loai_trichyeu=data['ten_loai_trichyeu'], tac_gia=data['tac_gia'],
                                   so_to=data['so_to'], ghi_chu=data['ghi_chu'], file_src_path=data['file_src'], id_=data.get('id'))
                # reload docs using current sort
                self.show_member_details(m)
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", str(e))

    def on_edit_document(self):
        doc = self.get_selected_doc()
        if not doc:
            QMessageBox.information(self, "Chọn", "Chọn hồ sơ để sửa")
            return
        dlg = DocumentDialog(self, document=doc)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            try:
                db.update_document(doc['id'], tt=data['tt'], so_ky_hieu=data['so_ky_hieu'], ngay_thang=data['ngay_thang'],
                                   ten_loai_trichyeu=data['ten_loai_trichyeu'], tac_gia=data['tac_gia'],
                                   so_to=data['so_to'], ghi_chu=data['ghi_chu'], file_src_path=data['file_src'])
                m = self.get_selected_member()
                if m:
                    self.show_member_details(m)
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", str(e))

    def on_delete_document(self):
        doc = self.get_selected_doc()
        if not doc:
            QMessageBox.information(self, "Chọn", "Chọn hồ sơ để xóa")
            return
        if QMessageBox.question(self, "Xác nhận", f"Xóa hồ sơ '{doc.get('ten_loai_trichyeu')}'?") == QMessageBox.StandardButton.Yes:
            db.delete_document(doc['id'])
            m = self.get_selected_member()
            if m:
                self.show_member_details(m)

    def on_open_document(self):
        doc = self.get_selected_doc()
        if not doc:
            QMessageBox.information(self, "Chọn", "Chọn hồ sơ có file để mở")
            return
        path = doc.get('file_path')
        if not path:
            QMessageBox.information(self, "No file", "Hồ sơ chưa gán file")
            return
        if not os.path.exists(path):
            QMessageBox.warning(self, "Không tìm thấy file", f"File không tồn tại: {path}")
            return
        try:
            if sys.platform.startswith('darwin'):
                os.system(f'open "{path}"')
            elif os.name == 'nt':
                os.startfile(path)
            else:
                os.system(f'xdg-open "{path}"')
        except Exception as e:
            QMessageBox.critical(self, "Lỗi mở file", str(e))

    # Search / filter (now pass order_by from members_sort)
    def on_search(self):
        name = self.search_input.text().strip()
        position = self.filter_position.text().strip()
        dept_id = self.filter_dept.currentData()
        has_docs = self.filter_has_docs.currentData()
        order_by = self.members_sort.currentData() or 'm.created_at DESC'
        results = db.search_members(name_contains=name if name else None,
                                    position_contains=position if position else None,
                                    department_id=dept_id,
                                    has_docs=has_docs,
                                    order_by=order_by)
        self.show_members_in_table(results)

    def on_clear_search(self):
        self.search_input.clear()
        self.filter_position.clear()
        self.filter_dept.setCurrentIndex(0)
        self.filter_has_docs.setCurrentIndex(0)
        self.members_sort.setCurrentIndex(0)
        self.docs_sort.setCurrentIndex(0)
        dept = self.get_selected_dept()
        if dept:
            self.load_members_for_dept(dept['id'])
        else:
            self.clear_member_views()

    def on_docs_sort_changed(self, idx):
        # reload docs for currently shown member
        m = self.get_selected_member()
        if m:
            self.show_member_details(m)

    # Export / Import / Reset handlers (same as before)
    def on_export_excel(self):
        dest, _ = QFileDialog.getSaveFileName(self, "Export Excel (.xlsx)", os.path.expanduser("~/export_data.xlsx"), "Excel Files (*.xlsx)")
        if not dest:
            return
        try:
            db.export_to_excel(dest)
            QMessageBox.information(self, "Hoàn tất", f"Export Excel thành công: {dest}")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", str(e))

    def on_export(self):
        dest, _ = QFileDialog.getSaveFileName(self, "Export dữ liệu (zip)", os.path.expanduser("~/export_data.zip"), "Zip Files (*.zip)")
        if not dest:
            return
        try:
            db.export_data_zip(dest)
            QMessageBox.information(self, "Hoàn tất", f"Export zip thành công: {dest}")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", str(e))

    def on_import_excel(self):
        src, _ = QFileDialog.getOpenFileName(self, "Chọn file Excel để import", "", "Excel Files (*.xlsx)")
        if not src:
            return
        clear_first = QMessageBox.question(self, "Xóa trước", "Bạn có muốn xóa dữ liệu hiện tại trước khi import không?\n(Yes = xóa rồi import, No = import vào dữ liệu hiện có)") == QMessageBox.StandardButton.Yes
        try:
            res = db.import_from_excel(src, clear_first=clear_first)
            msgs = [f"Departments: {res.get('departments')}", f"Members: {res.get('members')}", f"Documents: {res.get('documents')}"]
            if res.get('warnings'):
                msgs.append("Warnings:\n" + "\n".join(res.get('warnings')[:20]))
            QMessageBox.information(self, "Import hoàn tất", "\n".join(msgs))
            self.refresh_departments()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi import", str(e))

    def on_reset_db(self):
        reply = QMessageBox.question(self, "Reset DB", "Bạn muốn backup (export Excel) trước khi reset DB?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel)
        if reply == QMessageBox.StandardButton.Cancel:
            return
        backup_path = None
        if reply == QMessageBox.StandardButton.Yes:
            backup_path, _ = QFileDialog.getSaveFileName(self, "Chọn nơi lưu backup Excel", os.path.expanduser("~/backup_before_reset.xlsx"), "Excel Files (*.xlsx)")
            if not backup_path:
                return
        rm = QMessageBox.question(self, "Xóa files", "Bạn có muốn xóa luôn các file trong uploads không? (Yes = xóa file, No = giữ file)", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        remove_files = (rm == QMessageBox.StandardButton.Yes)
        try:
            db.reset_database(backup_excel_path=backup_path, remove_files=remove_files)
            QMessageBox.information(self, "Reset", "Đã reset database.")
            self.refresh_departments()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi reset", str(e))

    def on_about(self):
        QMessageBox.information(self, "Giới thiệu", "Ứng dụng Quản lý Phòng ban & Thành viên\n(Desktop, Python + PySide6)")

def main():
    db.init_db()
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()