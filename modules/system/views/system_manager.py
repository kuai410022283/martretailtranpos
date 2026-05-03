from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView,
    QLineEdit, QComboBox, QLabel, QMessageBox, QDialog,
    QFormLayout, QTabWidget, QFileDialog, QDateEdit, QSpinBox
)
from PyQt5.QtCore import Qt, QDate
from sqlalchemy.orm import Session
from modules.system.controllers import SystemController
from core.logger import logger
import os

class SystemManager(QWidget):
    def __init__(self, db_session: Session, current_user):
        super().__init__()
        self.db_session = db_session
        self.current_user = current_user
        self.controller = None
        self.users = []
        self.init_ui()
        self.init_controller()
        self.load_users()
        self.load_logs()
        self.load_backups()
        self.load_config()
    
    def init_controller(self):
        try:
            with self.db_session() as db:
                self.controller = SystemController(db)
        except Exception as e:
            logger.error(f"初始化系统控制器失败: {e}")
    
    def init_ui(self):
        self.setWindowTitle("系统管理")
        layout = QVBoxLayout()
        
        self.tab_widget = QTabWidget()
        
        self.user_tab = QWidget()
        self.init_user_tab()
        
        self.log_tab = QWidget()
        self.init_log_tab()
        
        self.backup_tab = QWidget()
        self.init_backup_tab()
        
        self.config_tab = QWidget()
        self.init_config_tab()
        
        self.tab_widget.addTab(self.user_tab, "用户管理")
        self.tab_widget.addTab(self.log_tab, "操作日志")
        self.tab_widget.addTab(self.backup_tab, "数据库备份")
        self.tab_widget.addTab(self.config_tab, "系统配置")
        
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)
    
    def init_user_tab(self):
        layout = QVBoxLayout()
        
        toolbar = QHBoxLayout()
        add_user_btn = QPushButton("新增用户")
        add_user_btn.clicked.connect(self.add_user)
        
        edit_user_btn = QPushButton("编辑用户")
        edit_user_btn.clicked.connect(self.edit_user)
        
        delete_user_btn = QPushButton("删除用户")
        delete_user_btn.clicked.connect(self.delete_user)
        
        toolbar.addStretch()
        toolbar.addWidget(add_user_btn)
        toolbar.addWidget(edit_user_btn)
        toolbar.addWidget(delete_user_btn)
        
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(6)
        self.user_table.setHorizontalHeaderLabels([
            "用户名", "真实姓名", "角色", "状态", "最后登录", "创建时间"])
        self.user_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.user_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.user_table.setAlternatingRowColors(True)
        
        layout.addLayout(toolbar)
        layout.addWidget(self.user_table)
        self.user_tab.setLayout(layout)
    
    def init_log_tab(self):
        layout = QVBoxLayout()
        
        toolbar = QHBoxLayout()
        refresh_log_btn = QPushButton("刷新")
        refresh_log_btn.clicked.connect(self.load_logs)
        toolbar.addStretch()
        toolbar.addWidget(refresh_log_btn)
        
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(5)
        self.log_table.setHorizontalHeaderLabels([
            "操作员", "模块", "操作", "内容", "时间"])
        self.log_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.log_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.log_table.setAlternatingRowColors(True)
        
        layout.addLayout(toolbar)
        layout.addWidget(self.log_table)
        self.log_tab.setLayout(layout)
    
    def init_backup_tab(self):
        layout = QVBoxLayout()
        
        toolbar = QHBoxLayout()
        backup_btn = QPushButton("创建备份")
        backup_btn.clicked.connect(self.create_backup)
        
        restore_btn = QPushButton("恢复备份")
        restore_btn.clicked.connect(self.restore_backup)
        
        delete_btn = QPushButton("删除备份")
        delete_btn.clicked.connect(self.delete_backup)
        
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.load_backups)
        
        toolbar.addStretch()
        toolbar.addWidget(backup_btn)
        toolbar.addWidget(restore_btn)
        toolbar.addWidget(delete_btn)
        toolbar.addWidget(refresh_btn)
        
        self.backup_table = QTableWidget()
        self.backup_table.setColumnCount(4)
        self.backup_table.setHorizontalHeaderLabels([
            "文件名", "大小", "创建时间", "路径"])
        self.backup_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.backup_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.backup_table.setAlternatingRowColors(True)
        
        layout.addLayout(toolbar)
        layout.addWidget(self.backup_table)
        self.backup_tab.setLayout(layout)
    
    def init_config_tab(self):
        layout = QVBoxLayout()
        
        form_layout = QFormLayout()
        
        # 数据库配置
        db_group = QWidget()
        db_layout = QFormLayout()
        self.db_path_input = QLineEdit()
        self.db_path_input.setPlaceholderText("数据库文件路径")
        db_layout.addRow("数据库路径:", self.db_path_input)
        db_group.setLayout(db_layout)
        
        # 系统配置
        sys_group = QWidget()
        sys_layout = QFormLayout()
        self.backup_dir_input = QLineEdit()
        self.backup_dir_input.setPlaceholderText("备份文件目录")
        sys_layout.addRow("备份目录:", self.backup_dir_input)
        
        self.session_timeout_input = QSpinBox()
        self.session_timeout_input.setRange(1, 120)
        self.session_timeout_input.setSuffix(" 分钟")
        sys_layout.addRow("会话超时:", self.session_timeout_input)
        sys_group.setLayout(sys_layout)
        
        form_layout.addRow(QLabel("<b>数据库配置</b>"))
        form_layout.addWidget(db_group)
        form_layout.addRow(QLabel("<b>系统配置</b>"))
        form_layout.addWidget(sys_group)
        
        buttons = QHBoxLayout()
        save_btn = QPushButton("保存配置")
        save_btn.clicked.connect(self.save_config)
        reload_btn = QPushButton("重载配置")
        reload_btn.clicked.connect(self.load_config)
        buttons.addStretch()
        buttons.addWidget(save_btn)
        buttons.addWidget(reload_btn)
        
        layout.addLayout(form_layout)
        layout.addLayout(buttons)
        self.config_tab.setLayout(layout)
    
    def load_users(self):
        if not self.controller:
            return
        
        try:
            self.users = self.controller.list_users()
            self.user_table.setRowCount(len(self.users))
            
            for row, user in enumerate(self.users):
                self.user_table.setItem(row, 0, QTableWidgetItem(user.username))
                self.user_table.setItem(row, 1, QTableWidgetItem(user.real_name or ""))
                self.user_table.setItem(row, 2, QTableWidgetItem(user.role))
                self.user_table.setItem(row, 3, QTableWidgetItem(user.status))
                
                last_login = user.last_login.strftime("%Y-%m-%d %H:%M") if user.last_login else ""
                self.user_table.setItem(row, 4, QTableWidgetItem(last_login))
                
                self.user_table.setItem(row, 5, QTableWidgetItem(
                    user.create_time.strftime("%Y-%m-%d %H:%M")))
                
                for col in range(6):
                    self.user_table.item(row, col).setFlags(
                        Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        
        except Exception as e:
            logger.error(f"加载用户列表失败: {e}")
    
    def load_logs(self):
        if not self.controller:
            return
        
        try:
            logs = self.controller.list_operation_logs()
            self.log_table.setRowCount(len(logs))
            
            for row, log in enumerate(logs):
                self.log_table.setItem(row, 0, QTableWidgetItem(log.operator or ""))
                self.log_table.setItem(row, 1, QTableWidgetItem(log.module or ""))
                self.log_table.setItem(row, 2, QTableWidgetItem(log.action or ""))
                self.log_table.setItem(row, 3, QTableWidgetItem(log.content or ""))
                self.log_table.setItem(row, 4, QTableWidgetItem(
                    log.create_time.strftime("%Y-%m-%d %H:%M")))
                
                for col in range(5):
                    self.log_table.item(row, col).setFlags(
                        Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        
        except Exception as e:
            logger.error(f"加载操作日志失败: {e}")
    
    def add_user(self):
        dialog = UserEditDialog(self.db_session, self, None)
        if dialog.exec_() == QDialog.Accepted:
            self.load_users()
            QMessageBox.information(self, "成功", "用户添加成功!")
    
    def edit_user(self):
        selected = self.user_table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要编辑的用户")
            return
        
        row = selected[0].row()
        user = self.users[row]
        
        dialog = UserEditDialog(self.db_session, self, user)
        if dialog.exec_() == QDialog.Accepted:
            self.load_users()
            QMessageBox.information(self, "成功", "用户更新成功!")
    
    def delete_user(self):
        selected = self.user_table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要删除的用户")
            return
        
        row = selected[0].row()
        user = self.users[row]
        
        if user.username == self.current_user.username:
            QMessageBox.warning(self, "提示", "不能删除当前登录用户")
            return
        
        reply = QMessageBox.question(
            self, "确认", f"确定要删除用户 {user.username} 吗？",
            QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                if self.controller.delete_user(user.id):
                    self.load_users()
                    QMessageBox.information(self, "成功", "用户已删除")
            except Exception as e:
                logger.error(f"删除用户失败: {e}")
                QMessageBox.critical(self, "错误", f"删除失败: {str(e)}")
    
    def create_backup(self):
        try:
            backup_file = self.controller.backup_database()
            self.load_backups()
            QMessageBox.information(self, "成功", f"数据库备份成功: {os.path.basename(backup_file)}")
        except Exception as e:
            logger.error(f"创建备份失败: {e}")
            QMessageBox.critical(self, "错误", f"创建备份失败: {str(e)}")
    
    def restore_backup(self):
        selected = self.backup_table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要恢复的备份")
            return
        
        row = selected[0].row()
        backup_path = self.backup_table.item(row, 3).text()
        
        reply = QMessageBox.question(
            self, "确认", f"确定要从备份恢复数据库吗？这将覆盖当前数据！",
            QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                self.controller.restore_database(backup_path)
                QMessageBox.information(self, "成功", "数据库恢复成功！")
            except Exception as e:
                logger.error(f"恢复备份失败: {e}")
                QMessageBox.critical(self, "错误", f"恢复备份失败: {str(e)}")
    
    def delete_backup(self):
        selected = self.backup_table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要删除的备份")
            return
        
        row = selected[0].row()
        backup_path = self.backup_table.item(row, 3).text()
        backup_name = self.backup_table.item(row, 0).text()
        
        reply = QMessageBox.question(
            self, "确认", f"确定要删除备份 {backup_name} 吗？",
            QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                self.controller.delete_backup(backup_path)
                self.load_backups()
                QMessageBox.information(self, "成功", "备份已删除")
            except Exception as e:
                logger.error(f"删除备份失败: {e}")
                QMessageBox.critical(self, "错误", f"删除备份失败: {str(e)}")
    
    def load_backups(self):
        if not self.controller:
            return
        
        try:
            backups = self.controller.list_backups()
            self.backup_table.setRowCount(len(backups))
            
            for row, backup in enumerate(backups):
                self.backup_table.setItem(row, 0, QTableWidgetItem(backup['filename']))
                size = backup['size'] / 1024 / 1024  # 转换为MB
                self.backup_table.setItem(row, 1, QTableWidgetItem(f"{size:.2f} MB"))
                self.backup_table.setItem(row, 2, QTableWidgetItem(backup['create_time'].strftime("%Y-%m-%d %H:%M:%S")))
                self.backup_table.setItem(row, 3, QTableWidgetItem(backup['filepath']))
                
                for col in range(4):
                    self.backup_table.item(row, col).setFlags(
                        Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        except Exception as e:
            logger.error(f"加载备份列表失败: {e}")
    
    def load_config(self):
        if not self.controller:
            return
        
        try:
            config = self.controller.get_config()
            db_config = config.get('database', {})
            self.db_path_input.setText(db_config.get('database_path', 'data/mrtpos.db'))
            
            sys_config = config.get('system', {})
            self.backup_dir_input.setText(sys_config.get('backup_dir', 'backups'))
            self.session_timeout_input.setValue(sys_config.get('session_timeout', 30))
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
    
    def save_config(self):
        if not self.controller:
            return
        
        try:
            # 更新配置
            self.controller.set_config('database.database_path', self.db_path_input.text().strip())
            self.controller.set_config('system.backup_dir', self.backup_dir_input.text().strip())
            self.controller.set_config('system.session_timeout', self.session_timeout_input.value())
            
            # 保存配置到文件
            self.controller.save_config()
            QMessageBox.information(self, "成功", "配置保存成功！")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            QMessageBox.critical(self, "错误", f"保存配置失败: {str(e)}")


class UserEditDialog(QDialog):
    def __init__(self, db_session, parent, user=None):
        super().__init__(parent)
        self.db_session = db_session
        self.user = user
        self.controller = None
        self.init_ui()
        self.init_controller()
        
        if user:
            self.setWindowTitle("编辑用户")
            self.load_user_data()
        else:
            self.setWindowTitle("新增用户")
    
    def init_controller(self):
        try:
            with self.db_session() as db:
                self.controller = SystemController(db)
        except Exception as e:
            logger.error(f"初始化控制器失败: {e}")
    
    def init_ui(self):
        layout = QFormLayout()
        
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.real_name_input = QLineEdit()
        
        self.role_combo = QComboBox()
        self.role_combo.addItems(["管理员", "收银员", "店员"])
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(["正常", "禁用"])
        
        layout.addRow("用户名 *:", self.username_input)
        layout.addRow("密码 *:", self.password_input)
        layout.addRow("真实姓名:", self.real_name_input)
        layout.addRow("角色:", self.role_combo)
        layout.addRow("状态:", self.status_combo)
        
        buttons = QHBoxLayout()
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.save_user)
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
    
    def load_user_data(self):
        self.username_input.setText(self.user.username)
        self.username_input.setReadOnly(True)
        self.password_input.setPlaceholderText("留空则不修改密码")
        self.real_name_input.setText(self.user.real_name or "")
        
        index = self.role_combo.findText(self.user.role)
        if index >= 0:
            self.role_combo.setCurrentIndex(index)
        
        index = self.status_combo.findText(self.user.status)
        if index >= 0:
            self.status_combo.setCurrentIndex(index)
    
    def save_user(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        if not username:
            QMessageBox.warning(self, "提示", "请输入用户名")
            return
        
        if not self.user and not password:
            QMessageBox.warning(self, "提示", "请输入密码")
            return
        
        try:
            data = {
                'username': username,
                'real_name': self.real_name_input.text().strip() or None,
                'role': self.role_combo.currentText(),
                'status': self.status_combo.currentText()
            }
            
            if password:
                data['password'] = password
            
            if self.user:
                self.controller.update_user(self.user.id, **data)
            else:
                self.controller.create_user(**data)
            
            self.accept()
        except Exception as e:
            logger.error(f"保存用户失败: {e}")
            QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")
