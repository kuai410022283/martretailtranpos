from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView,
    QLineEdit, QComboBox, QLabel, QMessageBox, QDialog,
    QFormLayout, QTabWidget, QDoubleSpinBox
)
from PyQt5.QtCore import Qt
from sqlalchemy.orm import Session
from shared.models.member import Member
from modules.member.controllers import MemberController
from core.logger import logger

class MemberManager(QWidget):
    def __init__(self, db_session: Session, current_user):
        super().__init__()
        self.db_session = db_session
        self.current_user = current_user
        self.members = []
        self.init_ui()
        self.load_members()
    
    def init_ui(self):
        self.setWindowTitle("会员管理")
        
        # 订阅销售完成事件，自动刷新数据
        from core.event_bus import subscribe_event
        subscribe_event("sale_completed", self.on_sale_completed)
        
        layout = QVBoxLayout()
        
        toolbar = QHBoxLayout()
        self.member_search = QLineEdit()
        self.member_search.setPlaceholderText("搜索会员...")
        self.member_search.textChanged.connect(self.filter_members)
        
        self.grade_combo = QComboBox()
        self.grade_combo.addItem("全部等级", None)
        self.grade_combo.addItem("普通会员", "普通会员")
        self.grade_combo.addItem("黄金会员", "黄金会员")
        self.grade_combo.addItem("白金会员", "白金会员")
        self.grade_combo.currentIndexChanged.connect(self.filter_members)
        
        add_btn = QPushButton("新增会员")
        add_btn.clicked.connect(self.add_member)
        
        edit_btn = QPushButton("编辑会员")
        edit_btn.clicked.connect(self.edit_member)
        
        delete_btn = QPushButton("删除会员")
        delete_btn.clicked.connect(self.delete_member)
        
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.load_members)
        
        toolbar.addWidget(QLabel("搜索:"))
        toolbar.addWidget(self.member_search)
        toolbar.addWidget(QLabel("等级:"))
        toolbar.addWidget(self.grade_combo)
        toolbar.addStretch()
        toolbar.addWidget(add_btn)
        toolbar.addWidget(edit_btn)
        toolbar.addWidget(delete_btn)
        toolbar.addWidget(refresh_btn)
        
        self.member_table = QTableWidget()
        self.member_table.setColumnCount(8)
        self.member_table.setHorizontalHeaderLabels([
            "会员编码", "姓名", "电话", "等级", 
            "积分", "余额", "备注", "创建时间"])
        self.member_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.member_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.member_table.setAlternatingRowColors(True)
        
        layout.addLayout(toolbar)
        layout.addWidget(self.member_table)
        self.setLayout(layout)
    
    def load_members(self):
        try:
            with self.db_session() as db:
                controller = MemberController(db)
                keyword = self.member_search.text().strip()
                grade = self.grade_combo.currentData()
                
                self.members = controller.list_members(
                    keyword=keyword if keyword else None,
                    grade=grade
                )
                
                self.member_table.setRowCount(len(self.members))
                
                for row, member in enumerate(self.members):
                    self.member_table.setItem(row, 0, QTableWidgetItem(member.code))
                    self.member_table.setItem(row, 1, QTableWidgetItem(member.name or ""))
                    self.member_table.setItem(row, 2, QTableWidgetItem(member.phone or ""))
                    self.member_table.setItem(row, 3, QTableWidgetItem(member.grade))
                    self.member_table.setItem(row, 4, QTableWidgetItem(str(member.points)))
                    self.member_table.setItem(row, 5, QTableWidgetItem(f"¥{member.balance:.2f}"))
                    self.member_table.setItem(row, 6, QTableWidgetItem(member.remark or ""))
                    self.member_table.setItem(row, 7, QTableWidgetItem(
                        member.create_time.strftime("%Y-%m-%d %H:%M")))
                    
                    for col in range(8):
                        self.member_table.item(row, col).setFlags(
                            Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        
        except Exception as e:
            logger.error(f"加载会员列表失败: {e}")
    
    def on_sale_completed(self, **kwargs):
        """当销售完成时触发，刷新会员数据"""
        logger.info("收到销售完成事件，正在刷新会员数据...")
        self.load_members()
    
    def filter_members(self):
        self.load_members()
    
    def add_member(self):
        dialog = MemberEditDialog(self.db_session, self, None)
        if dialog.exec_() == QDialog.Accepted:
            self.load_members()
            QMessageBox.information(self, "成功", "会员添加成功!")
    
    def edit_member(self):
        selected = self.member_table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要编辑的会员")
            return
        
        row = selected[0].row()
        member = self.members[row]
        
        dialog = MemberEditDialog(self.db_session, self, member)
        if dialog.exec_() == QDialog.Accepted:
            self.load_members()
            QMessageBox.information(self, "成功", "会员更新成功!")
    
    def delete_member(self):
        selected = self.member_table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要删除的会员")
            return
        
        row = selected[0].row()
        member = self.members[row]
        
        reply = QMessageBox.question(
            self, "确认", f"确定要删除会员 {member.name} 吗？",
            QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                with self.db_session() as db:
                    controller = MemberController(db)
                    if controller.delete_member(member.id):
                        self.load_members()
                        QMessageBox.information(self, "成功", "会员已删除")
            except Exception as e:
                logger.error(f"删除会员失败: {e}")
                QMessageBox.critical(self, "错误", f"删除失败: {str(e)}")


class MemberEditDialog(QDialog):
    def __init__(self, db_session, parent, member=None):
        super().__init__(parent)
        self.db_session = db_session
        self.member = member
        self.controller = None
        self.init_ui()
        self.init_controller()
        
        if member:
            self.setWindowTitle("编辑会员")
            self.load_member_data()
        else:
            self.setWindowTitle("新增会员")
    
    def init_controller(self):
        try:
            with self.db_session() as db:
                self.controller = MemberController(db)
        except Exception as e:
            logger.error(f"初始化控制器失败: {e}")
    
    def init_ui(self):
        layout = QFormLayout()
        
        self.code_input = QLineEdit()
        self.name_input = QLineEdit()
        self.phone_input = QLineEdit()
        
        self.grade_combo = QComboBox()
        self.grade_combo.addItems(["普通会员", "黄金会员", "白金会员"])
        
        self.points_input = QDoubleSpinBox()
        self.points_input.setRange(0, 999999)
        self.points_input.setDecimals(0)
        
        self.balance_input = QDoubleSpinBox()
        self.balance_input.setRange(0, 999999)
        self.balance_input.setDecimals(2)
        
        self.remark_input = QLineEdit()
        self.remark_input.setPlaceholderText("备注（可选）")
        
        layout.addRow("会员编码:", self.code_input)
        layout.addRow("姓名:", self.name_input)
        layout.addRow("电话:", self.phone_input)
        layout.addRow("等级:", self.grade_combo)
        layout.addRow("积分:", self.points_input)
        layout.addRow("余额:", self.balance_input)
        layout.addRow("备注:", self.remark_input)
        
        buttons = QHBoxLayout()
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.save_member)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        buttons.addStretch()
        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)
        
        main_layout = QVBoxLayout()
        main_layout.addLayout(layout)
        main_layout.addLayout(buttons)
        self.setLayout(main_layout)
        self.setMinimumWidth(400)
    
    def load_member_data(self):
        self.code_input.setText(self.member.code)
        self.code_input.setReadOnly(True)
        self.name_input.setText(self.member.name or "")
        self.phone_input.setText(self.member.phone or "")
        
        index = self.grade_combo.findText(self.member.grade)
        if index >= 0:
            self.grade_combo.setCurrentIndex(index)
        
        self.points_input.setValue(self.member.points)
        self.balance_input.setValue(self.member.balance)
        self.remark_input.setText(self.member.remark or "")
    
    def save_member(self):
        name = self.name_input.text().strip()
        phone = self.phone_input.text().strip()
        
        if not name:
            QMessageBox.warning(self, "提示", "请输入会员姓名")
            return
        
        try:
            data = {
                'code': self.code_input.text().strip(),
                'name': name,
                'phone': phone or None,
                'grade': self.grade_combo.currentText(),
                'points': self.points_input.value(),
                'balance': self.balance_input.value(),
                'remark': self.remark_input.text().strip() or None
            }
            
            if self.member:
                self.controller.update_member(self.member.id, **data)
            else:
                self.controller.create_member(**data)
            
            self.accept()
        except Exception as e:
            logger.error(f"保存会员失败: {e}")
            QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")
