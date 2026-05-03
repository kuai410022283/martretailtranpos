from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView,
    QLineEdit, QLabel, QMessageBox, QComboBox,
    QDialog, QFormLayout, QDoubleSpinBox, QGridLayout,
    QGroupBox, QSizePolicy, QScrollArea
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QEvent
from PyQt5.QtGui import QFont, QKeyEvent, QPalette, QColor, QDoubleValidator, QCursor
from sqlalchemy.orm import Session
from shared.models.product import Product
from modules.product.controllers import ProductController
from modules.pos.controllers import SaleController
from core.logger import logger

class ClickableLabel(QLabel):
    clicked = pyqtSignal()
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(event)

class POSWindow(QWidget):
    def __init__(self, db_session: Session, current_user):
        super().__init__()
        self.db_session = db_session
        self.current_user = current_user
        self.product_controller = None
        self.sale_controller = None
        self.cart_items = []
        self.suspended_orders = {}
        self.init_controllers()
        self.init_ui()
    
    def init_controllers(self):
        try:
            with self.db_session() as db:
                self.product_controller = ProductController(db)
                self.sale_controller = SaleController(db)
        except Exception as e:
            logger.error(f"初始化POS控制器失败: {e}")
    
    def init_ui(self):
        self.setWindowTitle("前台收银 - POS")
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f7fa;
            }
            QPushButton {
                padding: 12px 16px;
                background-color: #409eff;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #66b1ff;
            }
            QPushButton:pressed {
                background-color: #3a8ee6;
            }
            QPushButton#actionBtn {
                background-color: #e6a23c;
            }
            QPushButton#actionBtn:hover {
                background-color: #ebb563;
            }
            QPushButton#dangerBtn {
                background-color: #f56c6c;
            }
            QPushButton#dangerBtn:hover {
                background-color: #f78989;
            }
            QPushButton#successBtn {
                background-color: #67c23a;
            }
            QPushButton#successBtn:hover {
                background-color: #85ce61;
            }
            QPushButton#categoryBtn {
                background-color: #909399;
            }
            QPushButton#categoryBtn:hover {
                background-color: #a6a9ad;
            }
            QLineEdit {
                padding: 12px;
                border: 2px solid #dcdfe6;
                border-radius: 4px;
                background-color: white;
                font-size: 16px;
            }
            QLineEdit:focus {
                border-color: #409eff;
            }
            QTableWidget {
                background-color: white;
                border: 1px solid #e4e7ed;
                border-radius: 4px;
                gridline-color: #ebeef5;
            }
            QHeaderView::section {
                background-color: #f5f7fa;
                padding: 10px;
                border: none;
                border-bottom: 1px solid #e4e7ed;
                font-weight: bold;
            }
            QLabel {
                color: #606266;
            }
            QGroupBox {
                background-color: white;
                border: 1px solid #e4e7ed;
                border-radius: 4px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #606266;
                font-weight: bold;
            }
        """)
        
        main_layout = QHBoxLayout()
        main_layout.setSpacing(10)
        
        # 左侧面板
        left_panel = QVBoxLayout()
        left_panel.setSpacing(10)
        
        # 扫码/输入区域
        scan_layout = QHBoxLayout()
        scan_label = QLabel("条码/编码:")
        scan_label.setFont(QFont("Microsoft YaHei", 12))
        self.scan_input = QLineEdit()
        self.scan_input.setPlaceholderText("扫描条码或输入商品编码...")
        self.scan_input.setMinimumHeight(50)
        self.scan_input.returnPressed.connect(self.add_product_by_scan)
        scan_layout.addWidget(scan_label)
        scan_layout.addWidget(self.scan_input)
        
        # 商品分类快捷按钮
        category_group = QGroupBox("商品分类")
        category_layout = QGridLayout()
        category_layout.setSpacing(5)
        
        categories = []
        if self.product_controller:
            try:
                cat_objs = self.product_controller.get_categories()
                categories = [c.name for c in cat_objs]
            except Exception as e:
                logger.error(f"加载分类失败: {e}")
        
        if not categories:
             categories = ["饮料", "食品", "日用品", "文具", "电子产品", "服装", "生鲜", "熟食"]

        for i, category in enumerate(categories):
            btn = QPushButton(category)
            btn.setObjectName("categoryBtn")
            btn.setFixedSize(80, 40)
            btn.clicked.connect(lambda checked, cat=category: self.show_category_products(cat))
            category_layout.addWidget(btn, i // 4, i % 4)
        
        category_group.setLayout(category_layout)
        
        # 购物车表格
        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(5)
        self.cart_table.setHorizontalHeaderLabels(["商品名称", "单价", "数量", "小计", "操作"])
        self.cart_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cart_table.verticalHeader().setVisible(False)
        self.cart_table.setAlternatingRowColors(True)
        self.cart_table.cellChanged.connect(self.on_cart_cell_changed)
        
        # 操作按钮
        buttons_layout = QHBoxLayout()
        
        self.suspend_button = QPushButton("挂单 (F6)")
        self.suspend_button.setObjectName("actionBtn")
        self.suspend_button.clicked.connect(self.suspend_order)
        
        self.retrieve_button = QPushButton("取单 (F7)")
        self.retrieve_button.setObjectName("actionBtn")
        self.retrieve_button.clicked.connect(self.retrieve_order)
        
        self.clear_button = QPushButton("清空 (F8)")
        self.clear_button.setObjectName("dangerBtn")
        self.clear_button.clicked.connect(self.clear_cart)
        
        self.return_button = QPushButton("退货 (F9)")
        self.return_button.setObjectName("dangerBtn")
        self.return_button.clicked.connect(self.return_sale)
        
        buttons_layout.addWidget(self.suspend_button)
        buttons_layout.addWidget(self.retrieve_button)
        buttons_layout.addWidget(self.clear_button)
        buttons_layout.addWidget(self.return_button)
        
        left_panel.addLayout(scan_layout)
        left_panel.addWidget(category_group)
        left_panel.addWidget(self.cart_table)
        left_panel.addLayout(buttons_layout)
        
        # 右侧面板
        right_panel = QVBoxLayout()
        right_panel.setSpacing(15)
        
        # 信息面板
        info_panel = QWidget()
        info_panel.setStyleSheet("background-color: white; border-radius: 8px; padding: 12px;")
        info_layout = QVBoxLayout(info_panel)
        info_layout.setSpacing(12)
        
        # 合计金额 - 增大字体并添加视觉效果
        self.total_label = QLabel("合计: ¥0.00")
        self.total_label.setFont(QFont("Microsoft YaHei", 36, QFont.Bold))
        self.total_label.setStyleSheet("color: #f56c6c; font-size: 36px; font-weight: bold;")
        self.total_label.setAlignment(Qt.AlignCenter)
        
        self.item_count_label = QLabel("商品数量: 0")
        self.item_count_label.setFont(QFont("Microsoft YaHei", 14))
        self.item_count_label.setAlignment(Qt.AlignCenter)
        
        # 支付信息区域 - 使用卡片式垂直布局，更友好、更专业
        payment_section = QWidget()
        # 去除边框样式，仅使用白色背景
        payment_section.setStyleSheet("background-color: #ffffff; border: none; border-radius: 8px;")
        payment_layout = QVBoxLayout(payment_section)
        payment_layout.setContentsMargins(8, 8, 8, 8)
        payment_layout.setSpacing(16)
        
        # payment_title = QLabel("支付信息")
        # payment_title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        # payment_title.setStyleSheet("color: #303133;")
        # payment_layout.addWidget(payment_title)
        
        payment_grid = QGridLayout()
        payment_grid.setColumnStretch(0, 1)
        payment_grid.setColumnStretch(1, 3)
        payment_grid.setVerticalSpacing(12)
        payment_grid.setHorizontalSpacing(12)
        
        payment_label = QLabel("支付方式")
        payment_label.setFont(QFont("Microsoft YaHei", 13))
        payment_label.setStyleSheet("color: #606266;")
        self.payment_combo = QComboBox()
        self.payment_combo.addItems(["现金", "微信支付", "支付宝", "银行卡", "余额"])
        self.payment_combo.setMinimumHeight(48)
        self.payment_combo.setFont(QFont("Microsoft YaHei", 16))
        self.payment_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        payment_grid.addWidget(payment_label, 0, 0, alignment=Qt.AlignRight | Qt.AlignVCenter)
        payment_grid.addWidget(self.payment_combo, 0, 1)
        
        member_label = QLabel("会员")
        member_label.setFont(QFont("Microsoft YaHei", 13))
        member_label.setStyleSheet("color: #606266;")
        self.member_input = QLineEdit()
        self.member_input.setPlaceholderText("输入会员手机号或卡号")
        self.member_input.setMinimumHeight(48)
        self.member_input.setFont(QFont("Microsoft YaHei", 24))
        self.member_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        payment_grid.addWidget(member_label, 1, 0, alignment=Qt.AlignRight | Qt.AlignVCenter)
        payment_grid.addWidget(self.member_input, 1, 1)
        
        amount_label = QLabel("实收金额")
        amount_label.setFont(QFont("Microsoft YaHei", 13))
        amount_label.setStyleSheet("color: #606266;")
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("输入实收金额")
        self.amount_input.setMinimumHeight(48)
        self.amount_input.setFont(QFont("Microsoft YaHei", 24))
        self.amount_input.textChanged.connect(self.update_change)
        self.amount_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        validator = QDoubleValidator(0.0, 1000000000.0, 2, self.amount_input)
        validator.setNotation(QDoubleValidator.StandardNotation)
        self.amount_input.setValidator(validator)
        payment_grid.addWidget(amount_label, 2, 0, alignment=Qt.AlignRight | Qt.AlignVCenter)
        payment_grid.addWidget(self.amount_input, 2, 1)
        
        payment_layout.addLayout(payment_grid)
        
        # 将支付信息卡片加入信息面板（确保可见性）
        info_layout.addWidget(payment_section)
        
        # 找零显示 - 增大字体并添加视觉效果
        self.change_label = QLabel("找零: ¥0.00")
        self.change_label.setFont(QFont("Microsoft YaHei", 32, QFont.Bold))
        self.change_label.setStyleSheet("color: #67c23a; font-size: 32px; font-weight: bold;")
        self.change_label.setAlignment(Qt.AlignCenter)
        # 将金额合计、商品数量、找零置于支付信息卡片之前
        info_layout.addWidget(self.total_label)
        info_layout.addWidget(self.item_count_label)
        info_layout.addWidget(self.change_label)
        info_layout.addSpacing(8)
        # 添加支付信息卡片
        info_layout.addWidget(payment_section)
        
        # 结账按钮
        self.checkout_button = QPushButton("结账 (F5)")
        self.checkout_button.setObjectName("successBtn")
        self.checkout_button.setMinimumHeight(48)
        self.checkout_button.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        self.checkout_button.clicked.connect(self.checkout)
        
        # 数字键盘
        keypad_group = QGroupBox("数字键盘")
        keypad_layout = QGridLayout()
        keypad_layout.setSpacing(5)
        
        keypad_buttons = [
            ('1', 0, 0), ('2', 0, 1), ('3', 0, 2),
            ('4', 1, 0), ('5', 1, 1), ('6', 1, 2),
            ('7', 2, 0), ('8', 2, 1), ('9', 2, 2),
            ('.', 3, 0), ('0', 3, 1), ('C', 3, 2)
        ]
        
        for text, row, col in keypad_buttons:
            btn = QPushButton(text)
            btn.setFixedSize(70, 50)
            btn.setStyleSheet("font-size: 18px; font-weight: bold;")
            if text == 'C':
                btn.setObjectName("dangerBtn")
                btn.clicked.connect(self.clear_input)
            else:
                btn.clicked.connect(lambda checked, t=text: self.append_to_input(t))
            keypad_layout.addWidget(btn, row, col)
        
        keypad_group.setLayout(keypad_layout)
        
        # 使用滚动区域包装信息面板，避免内容被挤压导致不可见
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        scroll_area.setWidget(info_panel)
        right_panel.addWidget(scroll_area, stretch=3)
        right_panel.addWidget(self.checkout_button)
        right_panel.addWidget(keypad_group)
        right_panel.addStretch()
        
        # 组装主布局
        left_widget = QWidget()
        left_widget.setLayout(left_panel)
       # 右侧面板
        right_widget = QWidget()
        right_widget.setMinimumWidth(420)
        right_widget.setMaximumWidth(500)
        right_widget.setLayout(right_panel)
        
        main_layout.addWidget(left_widget, stretch=7)
        main_layout.addWidget(right_widget, stretch=3)
        
        self.setLayout(main_layout)
        
        # 设置焦点
        QTimer.singleShot(100, lambda: self.scan_input.setFocus())
    
    def add_product_by_scan(self):
        code = self.scan_input.text().strip()
        if not code:
            return
        
        try:
            with self.db_session() as db:
                controller = ProductController(db)
                product = controller.get_product_by_code(code)
                if not product:
                    product = controller.get_product_by_barcode(code)
                
                if product and product.status == '正常':
                    self.add_to_cart(product)
                    self.scan_input.clear()
                    QTimer.singleShot(100, lambda: self.scan_input.setFocus())
                else:
                    QMessageBox.warning(self, "提示", "未找到该商品或商品已停用")
        
        except Exception as e:
            logger.error(f"添加商品失败: {e}")
            QMessageBox.critical(self, "错误", f"添加商品失败: {str(e)}")
    
    def add_to_cart(self, product):
        for item in self.cart_items:
            if item['product_id'] == product.id:
                item['quantity'] += 1
                item['amount'] = item['quantity'] * item['price']
                self.update_cart_display()
                return
        
        self.cart_items.append({
            'product_id': product.id,
            'product_name': product.name,
            'price': product.price_sale,
            'quantity': 1,
            'amount': product.price_sale
        })
        
        self.update_cart_display()
        
    def on_cart_cell_changed(self, row, column):
        """处理购物车单元格修改"""
        if column == 2:  # Quantity column
            try:
                item = self.cart_table.item(row, column)
                if not item:
                    return
                
                text = item.text()
                new_qty = float(text)
                
                if new_qty <= 0:
                    QMessageBox.warning(self, "提示", "数量必须大于0")
                    self.update_cart_display()  # Revert
                    return

                # Update data
                self.cart_items[row]['quantity'] = new_qty
                self.cart_items[row]['amount'] = new_qty * self.cart_items[row]['price']
                
                # Update display
                self.update_cart_display()
                
            except ValueError:
                QMessageBox.warning(self, "错误", "请输入有效的数字")
                self.update_cart_display()  # Revert

    def update_cart_display(self):
        self.cart_table.blockSignals(True)
        self.cart_table.setRowCount(len(self.cart_items))
        
        total = 0.0
        count = 0.0
        
        for row, item in enumerate(self.cart_items):
            # Name (Not editable)
            name_item = QTableWidgetItem(item['product_name'])
            name_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.cart_table.setItem(row, 0, name_item)
            
            # Price (Not editable)
            price_item = QTableWidgetItem(f"¥{item['price']:.2f}")
            price_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.cart_table.setItem(row, 1, price_item)
            
            # Quantity (Editable)
            qty_item = QTableWidgetItem(f"{item['quantity']:.2f}")
            qty_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)
            qty_item.setBackground(QColor("#f0f9eb"))  # Light green background to indicate editability
            self.cart_table.setItem(row, 2, qty_item)
            
            # Amount (Not editable)
            amount_item = QTableWidgetItem(f"¥{item['amount']:.2f}")
            amount_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.cart_table.setItem(row, 3, amount_item)
            
            # 使用 ClickableLabel 代替 QPushButton
            delete_label = ClickableLabel("删除")
            delete_label.setAlignment(Qt.AlignCenter)
            delete_label.setStyleSheet("""
                QLabel {
                    color: #f56c6c;
                    font-weight: bold;
                    text-decoration: underline;
                }
                QLabel:hover {
                    color: #f78989;
                }
            """)
            delete_label.clicked.connect(lambda r=row: self.remove_from_cart(r))
            
            # 使用容器居中显示，避免样式被表格裁剪
            cell_container = QWidget()
            cell_layout = QHBoxLayout(cell_container)
            cell_layout.setContentsMargins(0, 0, 0, 0)
            cell_layout.setAlignment(Qt.AlignCenter)
            cell_layout.addWidget(delete_label)
            self.cart_table.setCellWidget(row, 4, cell_container)
            
            total += item['amount']
            count += item['quantity']
        
        self.cart_table.blockSignals(False)
        
        self.total_label.setText(f"合计: ¥{total:.2f}")
        self.item_count_label.setText(f"商品数量: {count:.2f}")
        
        # 更新找零金额
        self.update_change()
    
    def remove_from_cart(self, row):
        if 0 <= row < len(self.cart_items):
            self.cart_items.pop(row)
            self.update_cart_display()
    
    def clear_cart(self):
        if not self.cart_items:
            return
        
        reply = QMessageBox.question(
            self, "确认",
            "确定要清空购物车吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.cart_items = []
            self.update_cart_display()
    
    def suspend_order(self):
        if not self.cart_items:
            QMessageBox.warning(self, "提示", "购物车为空，无法挂单")
            return
        
        order_id = len(self.suspended_orders) + 1
        self.suspended_orders[order_id] = self.cart_items.copy()
        
        self.cart_items = []
        self.update_cart_display()
        
        QMessageBox.information(self, "成功", f"订单已挂起，挂单号: {order_id}")
    
    def retrieve_order(self):
        if not self.suspended_orders:
            QMessageBox.information(self, "提示", "没有挂起的订单")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("取单")
        layout = QVBoxLayout(dialog)
        
        combo = QComboBox()
        for order_id in self.suspended_orders.keys():
            combo.addItem(f"挂单号 {order_id}", order_id)
        
        buttons = QHBoxLayout()
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")
        buttons.addStretch()
        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)
        
        layout.addWidget(combo)
        layout.addLayout(buttons)
        
        def on_ok():
            order_id = combo.currentData()
            if order_id in self.suspended_orders:
                self.cart_items = self.suspended_orders[order_id]
                del self.suspended_orders[order_id]
                self.update_cart_display()
            dialog.accept()
        
        ok_btn.clicked.connect(on_ok)
        cancel_btn.clicked.connect(dialog.reject)
        
        dialog.exec_()
    
    def show_category_products(self, category):
        """显示分类商品"""
        try:
            with self.db_session() as db:
                controller = ProductController(db)
                
                # Get category by name
                cat_obj = controller.get_category_by_name(category)
                if not cat_obj:
                    QMessageBox.information(self, "提示", f"分类 '{category}' 不存在")
                    return
                
                products = controller.list_products(category_id=cat_obj.id)
                
                if not products:
                    QMessageBox.information(self, "提示", f"{category}分类下没有商品")
                    return
                
                # 创建商品选择对话框
                dialog = QDialog(self)
                dialog.setWindowTitle(f"选择{category}商品")
                dialog.setMinimumSize(600, 400)
                
                layout = QVBoxLayout(dialog)
                
                table = QTableWidget()
                table.setColumnCount(4)
                table.setHorizontalHeaderLabels(["商品编码", "商品名称", "价格", "操作"])
                table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
                
                table.setRowCount(len(products))
                for row, product in enumerate(products):
                    table.setItem(row, 0, QTableWidgetItem(product.code))
                    table.setItem(row, 1, QTableWidgetItem(product.name))
                    table.setItem(row, 2, QTableWidgetItem(f"¥{product.price_sale:.2f}"))
                    
                    # Use ClickableLabel instead of QPushButton
                    add_label = ClickableLabel("添加")
                    add_label.setAlignment(Qt.AlignCenter)
                    add_label.setStyleSheet("""
                        QLabel {
                            color: #67c23a;
                            font-weight: bold;
                            text-decoration: underline;
                        }
                        QLabel:hover {
                            color: #85ce61;
                        }
                    """)
                    add_label.clicked.connect(lambda p=product: (self.add_to_cart(p), dialog.accept()))
                    
                    add_container = QWidget()
                    add_layout = QHBoxLayout(add_container)
                    add_layout.setContentsMargins(0, 0, 0, 0)
                    add_layout.setAlignment(Qt.AlignCenter)
                    add_layout.addWidget(add_label)
                    table.setCellWidget(row, 3, add_container)
                
                layout.addWidget(table)
                
                dialog.exec_()
                
        except Exception as e:
            logger.error(f"显示分类商品失败: {e}")
            QMessageBox.critical(self, "错误", f"显示分类商品失败: {str(e)}")
    
    def return_sale(self):
        """退货功能"""
        QMessageBox.information(self, "提示", "退货功能开发中...")
    
    def append_to_input(self, text):
        """数字键盘输入"""
        # 确定当前焦点的输入框
        if self.scan_input.hasFocus():
            self.scan_input.insert(text)
        elif self.amount_input.hasFocus():
            self.amount_input.insert(text)
            # 自动更新找零
            self.update_change()
        elif self.member_input.hasFocus():
            self.member_input.insert(text)
        else:
            # 默认焦点到金额输入框
            self.amount_input.insert(text)
            self.amount_input.setFocus()
    
    def clear_input(self):
        """清空输入"""
        if self.scan_input.hasFocus():
            self.scan_input.clear()
        elif self.amount_input.hasFocus():
            self.amount_input.clear()
            self.update_change()
        elif self.member_input.hasFocus():
            self.member_input.clear()
        else:
            # 默认清空金额输入框
            self.amount_input.clear()
            self.update_change()
    
    def update_change(self):
        """更新找零金额"""
        try:
            total = sum(item['amount'] for item in self.cart_items)
            amount = float(self.amount_input.text()) if self.amount_input.text() else 0
            change = amount - total
            self.change_label.setText(f"找零: ¥{change:.2f}")
        except ValueError:
            self.change_label.setText("找零: ¥0.00")
    
    def keyPressEvent(self, event):
        """处理键盘事件"""
        key = event.key()
        
        if key == Qt.Key_F5:
            # F5 结账
            self.checkout()
        elif key == Qt.Key_F6:
            # F6 挂单
            self.suspend_order()
        elif key == Qt.Key_F7:
            # F7 取单
            self.retrieve_order()
        elif key == Qt.Key_F8:
            # F8 清空购物车
            self.clear_cart()
        elif key == Qt.Key_F9:
            # F9 退货
            self.return_sale()
        elif key == Qt.Key_Escape:
            # Esc 清空当前输入
            self.clear_input()
        elif key == Qt.Key_Tab:
            # Tab 切换输入焦点
            if self.scan_input.hasFocus():
                self.amount_input.setFocus()
            elif self.amount_input.hasFocus():
                self.member_input.setFocus()
            elif self.member_input.hasFocus():
                self.scan_input.setFocus()
        else:
            super().keyPressEvent(event)
    
    def checkout(self):
        if not self.cart_items:
            QMessageBox.warning(self, "提示", "购物车为空")
            return
        
        total = sum(item['amount'] for item in self.cart_items)
        
        # 检查实收金额
        if self.amount_input.text():
            try:
                received = float(self.amount_input.text())
                if received < total:
                    QMessageBox.warning(self, "提示", "实收金额不足")
                    return
            except ValueError:
                QMessageBox.warning(self, "提示", "请输入有效的实收金额")
                return
        
        reply = QMessageBox.question(
            self, "确认结账",
            f"合计金额: ¥{total:.2f}\n\n确定结账吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                with self.db_session() as db:
                    controller = SaleController(db)
                    sale_order = controller.create_sale_order(
                        items=self.cart_items,
                        payment_method=self.payment_combo.currentText(),
                        operator=self.current_user.username
                    )
                    
                    # 显示结账成功信息，包括找零
                    if self.amount_input.text():
                        received = float(self.amount_input.text())
                        change = received - total
                        QMessageBox.information(self, "成功", f"结账成功！\n单号: {sale_order.order_no}\n找零: ¥{change:.2f}")
                    else:
                        QMessageBox.information(self, "成功", f"结账成功！\n单号: {sale_order.order_no}")
                    
                    # 发布销售完成事件，通知其他模块更新数据
                    from core.event_bus import publish_event
                    publish_event("sale_completed", order_id=sale_order.id)
                    
                    # 清空购物车和输入
                    self.cart_items = []
                    self.update_cart_display()
                    self.amount_input.clear()
                    self.update_change()
                    
                    logger.info(f"结账成功: {sale_order.order_no}")
            
            except Exception as e:
                logger.error(f"结账失败: {e}")
                QMessageBox.critical(self, "错误", f"结账失败: {str(e)}")
