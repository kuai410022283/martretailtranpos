from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QStackedWidget, QMenuBar, 
    QMenu, QAction, QStatusBar, QMessageBox, QSplitter,
    QListWidget, QListWidgetItem, QToolButton, QApplication
)
from PyQt5.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QAbstractAnimation
from PyQt5.QtGui import QIcon, QFont, QColor, QPainter, QLinearGradient, QPen, QPixmap
from core.logger import logger
from core.event_bus import publish_event
import os

class MainWindow(QMainWindow):
    def __init__(self, db_session, current_user):
        super().__init__()
        self.db_session = db_session
        self.current_user = current_user
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle(f"MartRetailTranPOS - {self.current_user.real_name or self.current_user.username}")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1024, 768)
        
        # Load QSS
        try:
            import os
            style_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'styles', 'light.qss')
            with open(style_path, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            logger.error(f"Failed to load stylesheet: {e}")
            # Fallback inline style
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #f3f3f3;
                }
            """)
        
        self.create_menu_bar()
        self.create_main_content()
        self.create_status_bar()
        
        logger.info(f"主窗口已打开，用户: {self.current_user.username}")
    
    def create_menu_bar(self):
        menubar = self.menuBar()
        
        pos_menu = menubar.addMenu("&前台收银")
        pos_action = QAction("打开收银台", self)
        pos_action.setShortcut("F1")
        pos_action.triggered.connect(lambda: self.switch_to_module("pos"))
        pos_menu.addAction(pos_action)
        
        product_menu = menubar.addMenu("&商品管理")
        product_list_action = QAction("商品列表", self)
        product_list_action.triggered.connect(lambda: self.switch_to_module("product"))
        category_action = QAction("分类管理", self)
        category_action.triggered.connect(lambda: self.switch_to_module("product"))
        product_menu.addAction(product_list_action)
        product_menu.addAction(category_action)
        
        purchase_menu = menubar.addMenu("&采购管理")
        purchase_order_action = QAction("采购订单", self)
        purchase_order_action.triggered.connect(lambda: self.switch_to_module("purchase"))
        purchase_in_action = QAction("采购入库", self)
        purchase_in_action.triggered.connect(lambda: self.switch_to_module("purchase"))
        supplier_action = QAction("供应商管理", self)
        supplier_action.triggered.connect(lambda: self.switch_to_module("purchase"))
        purchase_menu.addAction(purchase_order_action)
        purchase_menu.addAction(purchase_in_action)
        purchase_menu.addAction(supplier_action)
        
        stock_menu = menubar.addMenu("&库存管理")
        stock_query_action = QAction("库存查询", self)
        stock_query_action.triggered.connect(lambda: self.switch_to_module("stock"))
        stock_check_action = QAction("库存盘点", self)
        stock_check_action.triggered.connect(lambda: self.switch_to_module("stock"))
        stock_log_action = QAction("库存变动", self)
        stock_log_action.triggered.connect(lambda: self.switch_to_module("stock"))
        stock_menu.addAction(stock_query_action)
        stock_menu.addAction(stock_check_action)
        stock_menu.addAction(stock_log_action)
        
        sale_menu = menubar.addMenu("&销售管理")
        sale_query_action = QAction("销售记录", self)
        sale_query_action.triggered.connect(lambda: self.switch_to_module("sale"))
        sale_report_action = QAction("销售报表", self)
        sale_report_action.triggered.connect(lambda: self.switch_to_module("sale"))
        sale_menu.addAction(sale_query_action)
        sale_menu.addAction(sale_report_action)
        
        member_menu = menubar.addMenu("&会员管理")
        member_list_action = QAction("会员列表", self)
        member_list_action.triggered.connect(lambda: self.switch_to_module("member"))
        member_menu.addAction(member_list_action)
        
        finance_menu = menubar.addMenu("&财务管理")
        finance_action = QAction("财务流水", self)
        finance_action.triggered.connect(lambda: self.switch_to_module("finance"))
        finance_menu.addAction(finance_action)
        
        system_menu = menubar.addMenu("&系统管理")
        user_action = QAction("用户管理", self)
        user_action.triggered.connect(lambda: self.switch_to_module("system"))
        log_action = QAction("操作日志", self)
        log_action.triggered.connect(lambda: self.switch_to_module("system"))
        backup_action = QAction("数据备份", self)
        backup_action.triggered.connect(lambda: self.switch_to_module("system"))
        system_menu.addAction(user_action)
        system_menu.addAction(log_action)
        system_menu.addAction(backup_action)
        
        help_menu = menubar.addMenu("&帮助")
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_main_content(self):
        # Create main splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        
        # Sidebar Container
        sidebar_container = QWidget()
        sidebar_container.setObjectName("sidebarContainer")
        sidebar_container.setStyleSheet("background-color: #f3f3f3; border-right: 1px solid #e5e5e5;")
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        # Sidebar Header
        sidebar_header = QWidget()
        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(16, 24, 16, 24)
        
        # Logo & Title Container
        title_container = QWidget()
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(10)
        
        # Load Icon
        # Use QToolButton for better high-DPI icon rendering than QLabel+QPixmap
        icon_btn = QToolButton()
        icon_btn.setIconSize(QSize(32, 32))
        icon_btn.setStyleSheet("border: none; background: transparent; padding: 0;")
        icon_btn.setAttribute(Qt.WA_TransparentForMouseEvents, True) # Make it non-interactive
        
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        icon_candidates = [
            os.path.join(base_dir, 'resources', 'icons', 'app.ico'),
            os.path.join(base_dir, 'resources', 'icon.png'),
            os.path.join(base_dir, 'resources', 'icon.svg')
        ]
        
        for icon_path in icon_candidates:
            if os.path.exists(icon_path):
                icon_btn.setIcon(QIcon(icon_path))
                break
        
        logo_label = QLabel("MRTPOS") # 全称MartRetailTranPOS
        logo_label.setObjectName("titleLabel")
        logo_label.setFont(QFont("Segoe UI Variable Display", 16, QFont.Bold))
        
        title_layout.addWidget(icon_btn)
        title_layout.addWidget(logo_label)
        title_layout.addStretch()
        
        subtitle_label = QLabel("超市零售管理系统")
        subtitle_label.setObjectName("subtitleLabel")
        subtitle_label.setStyleSheet("color: #5d5d5d; margin-top: 4px;")
        
        header_layout.addWidget(title_container)
        header_layout.addWidget(subtitle_label)
        sidebar_header.setLayout(header_layout)
        
        # Sidebar List
        self.sidebar = QListWidget()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(200) # Windows 11 NavigationView standard width
        self.sidebar.setFrameShape(QListWidget.NoFrame)
        self.sidebar.setFocusPolicy(Qt.NoFocus)
        
        modules = [
            ("pos", "🛒 前台收银"),
            ("product", "📦 商品管理"),
            ("purchase", "📥 采购管理"),
            ("stock", "📊 库存管理"),
            ("sale", "💰 销售管理"),
            ("member", "👥 会员管理"),
            ("finance", "💳 财务管理"),
            ("system", "⚙️ 系统管理")
        ]
        
        for module_id, module_name in modules:
            item = QListWidgetItem(module_name)
            item.setData(Qt.UserRole, module_id)
            item.setSizeHint(QSize(0, 40)) # Taller items
            self.sidebar.addItem(item)
        
        self.sidebar.currentRowChanged.connect(self.on_sidebar_changed)
        
        # Assemble Sidebar
        sidebar_layout.addWidget(sidebar_header)
        sidebar_layout.addWidget(self.sidebar)
        # Removed addStretch() to allow sidebar to expand
        
        # User Info at bottom of sidebar
        user_widget = QWidget()
        user_layout = QHBoxLayout()
        user_layout.setContentsMargins(16, 16, 16, 16)
        user_avatar = QLabel("👤")
        user_avatar.setFont(QFont("Segoe UI Emoji", 20))
        user_info = QLabel(f"{self.current_user.real_name}\n{self.current_user.role}")
        user_info.setStyleSheet("color: #5d5d5d; font-size: 12px;")
        user_layout.addWidget(user_avatar)
        user_layout.addWidget(user_info)
        user_layout.addStretch()
        user_widget.setLayout(user_layout)
        sidebar_layout.addWidget(user_widget)

        sidebar_container.setLayout(sidebar_layout)
        
        # Main Content Area
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("background-color: #f3f3f3;") # Matches window background
        
        # Welcome Page
        welcome_widget = self.create_welcome_widget()
        self.stacked_widget.addWidget(welcome_widget)
        
        # Add to splitter
        splitter.addWidget(sidebar_container)
        splitter.addWidget(self.stacked_widget)
        splitter.setStretchFactor(1, 1)
        splitter.setCollapsible(0, False)
        
        self.setCentralWidget(splitter)
    
    def create_welcome_widget(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(50, 50, 50, 50)
        
        # Main Title
        welcome_label = QLabel("欢迎使用")
        welcome_label.setFont(QFont("Segoe UI Variable Display", 28, QFont.Bold))
        welcome_label.setAlignment(Qt.AlignLeft)
        
        # System Name
        system_label = QLabel("MartRetailTranPOS")
        system_label.setObjectName("titleLabel")
        system_label.setFont(QFont("Segoe UI Variable Display", 36, QFont.Bold))
        system_label.setAlignment(Qt.AlignLeft)
        system_label.setStyleSheet("color: #0067c0; margin-bottom: 20px;")
        
        # Subtitle
        desc_label = QLabel("超市零售进销存管理系统")
        desc_label.setObjectName("subtitleLabel")
        desc_label.setFont(QFont("Segoe UI Variable Text", 16))
        desc_label.setAlignment(Qt.AlignLeft)
        desc_label.setStyleSheet("margin-bottom: 40px;")
        
        # Quick Access
        quick_access_layout = QHBoxLayout()
        quick_access_layout.setSpacing(20)
        quick_access_layout.setAlignment(Qt.AlignLeft)
        
        # POS Card
        pos_widget = QPushButton() # Use QPushButton for interactive card
        pos_widget.setFixedSize(200, 150)
        pos_widget.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                border: 1px solid #e5e5e5;
                border-radius: 8px;
                text-align: center;
                padding: 20px;
            }
            QPushButton:hover {
                background-color: #fbfbfb;
                border: 1px solid #d1d1d1;
            }
        """)
        
        pos_layout = QVBoxLayout()
        pos_layout.setAlignment(Qt.AlignCenter)
        pos_layout.setContentsMargins(0, 0, 0, 0)
        pos_layout.setSpacing(10)
        
        pos_icon = QLabel("🛒")
        pos_icon.setFont(QFont("Segoe UI Emoji", 32))
        pos_icon.setAlignment(Qt.AlignCenter)
        pos_icon.setStyleSheet("background: transparent; border: none;")
        
        pos_name = QLabel("前台收银")
        pos_name.setFont(QFont("Segoe UI Variable Text", 12, QFont.Bold))
        pos_name.setAlignment(Qt.AlignCenter)
        pos_name.setStyleSheet("color: #202020; background: transparent; border: none;")
        pos_name.setWordWrap(True)
        
        pos_layout.addWidget(pos_icon)
        pos_layout.addWidget(pos_name)
        pos_widget.setLayout(pos_layout)
        
        pos_widget.clicked.connect(lambda: self.switch_to_module("pos"))
        pos_widget.setCursor(Qt.PointingHandCursor)
        
        quick_access_layout.addWidget(pos_widget)
        
        layout.addWidget(welcome_label)
        layout.addWidget(system_label)
        layout.addWidget(desc_label)
        layout.addLayout(quick_access_layout)
        
        widget.setLayout(layout)
        return widget
    
    def create_status_bar(self):
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #ffffff;
                border-top: 1px solid #e9ecef;
                font-family: 'Microsoft YaHei';
                font-size: 12px;
                padding: 0 16px;
            }
            QStatusBar QLabel {
                color: #495057;
                padding: 0 8px;
            }
        """)
        self.setStatusBar(self.status_bar)
        
        # 左侧状态信息
        system_label = QLabel("系统就绪")
        self.status_bar.addWidget(system_label)
        
        # 中间分隔
        self.status_bar.addWidget(QLabel("|"))
        
        # 右侧用户信息
        user_label = QLabel(f"当前用户: {self.current_user.real_name or self.current_user.username} ({self.current_user.role})")
        self.status_bar.addPermanentWidget(user_label)
        
        # 显示当前时间
        from datetime import datetime
        time_label = QLabel(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.status_bar.addPermanentWidget(time_label)
        
        # 定时更新时间
        from PyQt5.QtCore import QTimer
        self.time_timer = QTimer(self)
        self.time_timer.timeout.connect(lambda: time_label.setText(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        self.time_timer.start(1000)
        
        self.status_bar.showMessage("系统就绪", 3000)
    
    def on_sidebar_changed(self, index):
        item = self.sidebar.item(index)
        if item:
            module_id = item.data(Qt.UserRole)
            self.switch_to_module(module_id)
    
    def switch_to_module(self, module_id):
        from core.service_registry import has_service, get_service
        
        module_widgets = {
            "pos": self.load_pos_module,
            "product": self.load_product_module,
            "purchase": self.load_purchase_module,
            "stock": self.load_stock_module,
            "sale": self.load_sale_module,
            "member": self.load_member_module,
            "finance": self.load_finance_module,
            "system": self.load_system_module
        }
        
        if module_id in module_widgets:
            try:
                # 加载模块
                widget = module_widgets[module_id]()
                # 触发事件
                publish_event('module_switched', module_id=module_id)
                # 显示状态信息
                self.status_bar.showMessage(f"已切换到 {module_id} 模块", 2000)
            except Exception as e:
                logger.error(f"切换到模块 {module_id} 失败: {e}", exc_info=True)
                QMessageBox.critical(self, "错误", f"无法加载模块 {module_id}:\n{str(e)}")
        
    def load_pos_module(self):
        from modules.pos.views.pos_window import POSWindow
        widget = POSWindow(self.db_session, self.current_user)
        return self.add_widget_with_animation(widget, "pos")
    
    def load_product_module(self):
        from modules.product.views.product_manager import ProductManager
        widget = ProductManager(self.db_session, self.current_user)
        return self.add_widget_with_animation(widget, "product")
    
    def load_purchase_module(self):
        from modules.purchase.views.purchase_manager import PurchaseManager
        widget = PurchaseManager(self.db_session, self.current_user)
        return self.add_widget_with_animation(widget, "purchase")
    
    def load_stock_module(self):
        from modules.stock.views.stock_manager import StockManager
        widget = StockManager(self.db_session, self.current_user)
        return self.add_widget_with_animation(widget, "stock")
    
    def load_sale_module(self):
        from modules.sale.views.sale_manager import SaleManager
        widget = SaleManager(self.db_session, self.current_user)
        return self.add_widget_with_animation(widget, "sale")
    
    def load_member_module(self):
        from modules.member.views.member_manager import MemberManager
        widget = MemberManager(self.db_session, self.current_user)
        return self.add_widget_with_animation(widget, "member")
    
    def load_finance_module(self):
        from modules.finance.views.finance_manager import FinanceManager
        widget = FinanceManager(self.db_session, self.current_user)
        return self.add_widget_with_animation(widget, "finance")
    
    def load_system_module(self):
        from modules.system.views.system_manager import SystemManager
        widget = SystemManager(self.db_session, self.current_user)
        return self.add_widget_with_animation(widget, "system")
    
    def add_widget_with_animation(self, widget, module_id):
        """添加并显示模块窗口"""
        # 检查是否已存在该模块的窗口
        for i in range(self.stacked_widget.count()):
            existing_widget = self.stacked_widget.widget(i)
            if hasattr(existing_widget, "module_id") and existing_widget.module_id == module_id:
                # 已有该模块窗口，直接切换
                self.stacked_widget.setCurrentIndex(i)
                return existing_widget
        
        # 添加新窗口
        widget.module_id = module_id
        self.stacked_widget.addWidget(widget)
        self.stacked_widget.setCurrentWidget(widget)
        return widget
    
    def animate_widget_switch(self, target_index):
        """窗口切换（移除不稳定的动画效果）"""
        self.stacked_widget.setCurrentIndex(target_index)
    
    def show_about(self):
        QMessageBox.about(
            self,
            "关于 MartRetailTranPOS",
            "<h3>MartRetailTranPOS v1.0.0</h3>"
            "<p>超市零售进销存管理系统</p>"
            "<p>适用于单店或中小型连锁超市的进销存管理</p>"
            "<p>© 2026 All Rights Reserved</p>"
        )
    
    def closeEvent(self, event):
        reply = QMessageBox.question(
            self, "确认退出", 
            "确定要退出系统吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            publish_event('app_closing')
            logger.info(f"用户退出系统: {self.current_user.username}")
            event.accept()
        else:
            event.ignore()
