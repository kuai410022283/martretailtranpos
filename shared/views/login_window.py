from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QFrame, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QColor
from shared.services.auth_service import AuthService
from core.logger import logger
import os

class LoginWindow(QWidget):
    def __init__(self, db_session):
        super().__init__()
        self.db_session = db_session
        self.auth_service = AuthService(db_session)
        self.current_user = None
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("MartRetailTranPOS - 登录")
        self.setFixedSize(450, 420)
        self.setObjectName("LoginWindow")
        
        # Load QSS
        try:
            style_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'styles', 'light.qss')
            with open(style_path, 'r', encoding='utf-8') as f:
                qss = f.read()
                # 强制设置 LoginWindow 背景色，覆盖 QWidget 全局透明设置
                qss += "\nQWidget#LoginWindow { background-color: #f3f3f3; }"
                self.setStyleSheet(qss)
        except Exception as e:
            logger.error(f"Failed to load stylesheet: {e}")
            self.setStyleSheet("background-color: #f3f3f3;")

        # Main Layout
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.setContentsMargins(0, 0, 0, 0)
        # 确保登录窗口为浅色背景
        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(self.backgroundRole(), QColor("#f3f3f3"))
        self.setPalette(pal)
        
        # Login Card
        card = QFrame()
        card.setObjectName("LoginCard")
        card.setStyleSheet("""
            QFrame#LoginCard {
                background-color: #ffffff;
                border: 1px solid #e5e5e5;
                border-radius: 8px;
            }
        """)
        card.setFixedSize(360, 340)
        
        # Shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(0, 4)
        card.setGraphicsEffect(shadow)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(20)
        
        # Title
        title_label = QLabel("MartRetailTranPOS")
        title_label.setFont(QFont("Segoe UI Variable Display", 20, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #0067c0;")
        
        subtitle_label = QLabel("超市零售管理系统")
        subtitle_label.setFont(QFont("Segoe UI Variable Text", 12))
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("color: #5d5d5d;")
        
        # Form
        form_layout = QVBoxLayout()
        form_layout.setSpacing(15)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("用户名")
        self.username_input.setFixedHeight(40)
        self.username_input.setText("admin") # Default for convenience
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("密码")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(40)
        self.password_input.setText("admin123")
        
        form_layout.addWidget(self.username_input)
        form_layout.addWidget(self.password_input)
        
        # Login Button
        self.login_button = QPushButton("登 录")
        self.login_button.setObjectName("primaryButton")
        self.login_button.setFixedHeight(45)
        self.login_button.setFont(QFont("Segoe UI Variable Text", 14, QFont.Bold))
        self.login_button.setCursor(Qt.PointingHandCursor)
        self.login_button.clicked.connect(self.handle_login)
        
        # Default tip
        tip_label = QLabel("默认账号: admin / admin123")
        tip_label.setAlignment(Qt.AlignCenter)
        tip_label.setStyleSheet("color: #909399; font-size: 12px;")
        
        # Assemble Card
        card_layout.addWidget(title_label)
        card_layout.addWidget(subtitle_label)
        card_layout.addLayout(form_layout)
        card_layout.addWidget(self.login_button)
        card_layout.addWidget(tip_label)
        card_layout.addStretch()
        
        main_layout.addWidget(card)
        self.setLayout(main_layout)
        
        # Enter key support
        self.password_input.returnPressed.connect(self.handle_login)
        self.username_input.returnPressed.connect(lambda: self.password_input.setFocus())
    
    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username:
            QMessageBox.warning(self, "提示", "请输入用户名")
            self.username_input.setFocus()
            return
        
        if not password:
            QMessageBox.warning(self, "提示", "请输入密码")
            self.password_input.setFocus()
            return
        
        try:
            user = self.auth_service.authenticate(username, password)
            
            if user:
                logger.info(f"用户登录成功: {username}")
                self.current_user = user
                self.open_main_window()
            else:
                QMessageBox.warning(self, "登录失败", "用户名或密码错误")
                self.password_input.clear()
                self.password_input.setFocus()
        
        except Exception as e:
            logger.error(f"登录错误: {e}", exc_info=True)
            QMessageBox.critical(self, "错误", f"登录失败: {str(e)}")
    
    def open_main_window(self):
        from .main_window import MainWindow
        
        self.main_window = MainWindow(self.db_session, self.current_user)
        self.main_window.showMaximized()
        self.close()
