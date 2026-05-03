from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView,
    QLineEdit, QComboBox, QLabel, QMessageBox, QDialog,
    QFormLayout, QTextEdit, QTabWidget, QDoubleSpinBox,
    QSpinBox, QSplitter
)
from PyQt5.QtCore import Qt
from sqlalchemy.orm import Session
from shared.models.supplier import Supplier
from shared.models.purchase import PurchaseOrder, PurchaseItem
from shared.models.product import Product
from modules.purchase.controllers import PurchaseController
from modules.product.controllers import ProductController
from core.logger import logger

class PurchaseManager(QWidget):
    def __init__(self, db_session: Session, current_user):
        super().__init__()
        self.db_session = db_session
        self.current_user = current_user
        self.controller = None
        self.product_controller = None
        self.init_ui()
        self.init_controller()
        self.load_suppliers()
        self.load_purchase_orders()
    
    def init_controller(self):
        try:
            with self.db_session() as db:
                self.controller = PurchaseController(db)
                self.product_controller = ProductController(db)
        except Exception as e:
            logger.error(f"初始化控制器失败: {e}")
    
    def init_ui(self):
        self.setWindowTitle("采购管理")
        layout = QVBoxLayout()
        
        self.tab_widget = QTabWidget()
        
        self.supplier_tab = QWidget()
        self.suppliers = []
        self.init_supplier_tab()
        
        self.purchase_tab = QWidget()
        self.purchase_orders = []
        self.init_purchase_tab()
        
        self.tab_widget.addTab(self.supplier_tab, "供应商管理")
        self.tab_widget.addTab(self.purchase_tab, "采购订单")
        
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)
    
    def init_supplier_tab(self):
        layout = QVBoxLayout()
        
        toolbar = QHBoxLayout()
        self.supplier_search = QLineEdit()
        self.supplier_search.setPlaceholderText("搜索供应商...")
        self.supplier_search.textChanged.connect(self.filter_suppliers)
        
        add_supplier_btn = QPushButton("新增供应商")
        add_supplier_btn.clicked.connect(self.add_supplier)
        
        edit_supplier_btn = QPushButton("编辑供应商")
        edit_supplier_btn.clicked.connect(self.edit_supplier)
        
        delete_supplier_btn = QPushButton("删除供应商")
        delete_supplier_btn.clicked.connect(self.delete_supplier)
        
        toolbar.addWidget(QLabel("搜索:"))
        toolbar.addWidget(self.supplier_search)
        toolbar.addStretch()
        toolbar.addWidget(add_supplier_btn)
        toolbar.addWidget(edit_supplier_btn)
        toolbar.addWidget(delete_supplier_btn)
        
        self.supplier_table = QTableWidget()
        self.supplier_table.setColumnCount(6)
        self.supplier_table.setHorizontalHeaderLabels(["供应商编码", "供应商名称", "联系人", "电话", "地址", "创建时间"])
        self.supplier_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.supplier_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.supplier_table.setAlternatingRowColors(True)
        
        layout.addLayout(toolbar)
        layout.addWidget(self.supplier_table)
        self.supplier_tab.setLayout(layout)
    
    def init_purchase_tab(self):
        layout = QVBoxLayout()
        
        toolbar = QHBoxLayout()
        self.purchase_status = QComboBox()
        self.purchase_status.addItem("全部状态", None)
        self.purchase_status.addItem("待入库", "待入库")
        self.purchase_status.addItem("已完成", "已完成")
        self.purchase_status.currentIndexChanged.connect(self.filter_purchase_orders)
        
        self.purchase_search = QLineEdit()
        self.purchase_search.setPlaceholderText("搜索订单号...")
        self.purchase_search.textChanged.connect(self.filter_purchase_orders)
        
        add_purchase_btn = QPushButton("新建采购单")
        add_purchase_btn.clicked.connect(self.add_purchase_order)

        edit_purchase_btn = QPushButton("编辑")
        edit_purchase_btn.clicked.connect(self.edit_purchase_order)
        
        receive_btn = QPushButton("入库/确认")
        receive_btn.clicked.connect(self.receive_purchase_order)
        
        return_btn = QPushButton("采购退货")
        return_btn.clicked.connect(self.return_purchase_order)
        
        detail_btn = QPushButton("查看详情")
        detail_btn.clicked.connect(self.view_purchase_detail)
        
        toolbar.addWidget(QLabel("状态:"))
        toolbar.addWidget(self.purchase_status)
        toolbar.addWidget(QLabel("搜索:"))
        toolbar.addWidget(self.purchase_search)
        toolbar.addStretch()
        toolbar.addWidget(add_purchase_btn)
        toolbar.addWidget(edit_purchase_btn)
        toolbar.addWidget(receive_btn)
        toolbar.addWidget(return_btn)
        toolbar.addWidget(detail_btn)
        
        self.purchase_table = QTableWidget()
        self.purchase_table.setColumnCount(8)
        self.purchase_table.setHorizontalHeaderLabels(
            ["订单号", "类型", "供应商", "总金额", "状态", "创建时间", "完成时间", "备注"])
        self.purchase_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.purchase_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.purchase_table.setAlternatingRowColors(True)
        
        layout.addLayout(toolbar)
        layout.addWidget(self.purchase_table)
        self.purchase_tab.setLayout(layout)
    
    def load_suppliers(self):
        if not self.controller:
            return
        
        try:
            keyword = self.supplier_search.text().strip()
            self.suppliers = self.controller.list_suppliers(keyword if keyword else None)
            self.supplier_table.setRowCount(len(self.suppliers))
            
            for row, supplier in enumerate(self.suppliers):
                self.supplier_table.setItem(row, 0, QTableWidgetItem(supplier.code))
                self.supplier_table.setItem(row, 1, QTableWidgetItem(supplier.name))
                self.supplier_table.setItem(row, 2, QTableWidgetItem(supplier.contact or ""))
                self.supplier_table.setItem(row, 3, QTableWidgetItem(supplier.phone or ""))
                self.supplier_table.setItem(row, 4, QTableWidgetItem(supplier.address or ""))
                self.supplier_table.setItem(row, 5, QTableWidgetItem(
                    supplier.create_time.strftime("%Y-%m-%d %H:%M")))
                
                for col in range(6):
                    self.supplier_table.item(row, col).setFlags(
                        Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        except Exception as e:
            logger.error(f"加载供应商列表失败: {e}")
    
    def filter_suppliers(self):
        self.load_suppliers()
    
    def load_purchase_orders(self):
        if not self.controller:
            return
        
        try:
            status = self.purchase_status.currentData()
            keyword = self.purchase_search.text().strip()
            self.purchase_orders = self.controller.list_purchase_orders(status=status, keyword=keyword)
            self.purchase_table.setRowCount(len(self.purchase_orders))
            
            for row, order in enumerate(self.purchase_orders):
                self.purchase_table.setItem(row, 0, QTableWidgetItem(order.order_no))
                
                order_type = getattr(order, 'order_type', '采购')
                self.purchase_table.setItem(row, 1, QTableWidgetItem(order_type))
                
                supplier_name = order.supplier.name if order.supplier else ""
                self.purchase_table.setItem(row, 2, QTableWidgetItem(supplier_name))
                self.purchase_table.setItem(row, 3, QTableWidgetItem(f"¥{order.total_amount:.2f}"))
                self.purchase_table.setItem(row, 4, QTableWidgetItem(order.status))
                self.purchase_table.setItem(row, 5, QTableWidgetItem(
                    order.create_time.strftime("%Y-%m-%d %H:%M")))
                finish_time = order.finish_time.strftime("%Y-%m-%d %H:%M") if order.finish_time else ""
                self.purchase_table.setItem(row, 6, QTableWidgetItem(finish_time))
                self.purchase_table.setItem(row, 7, QTableWidgetItem(order.remark or ""))
                
                for col in range(8):
                    self.purchase_table.item(row, col).setFlags(
                        Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        except Exception as e:
            logger.error(f"加载采购订单失败: {e}")
    
    def view_purchase_detail(self):
        selected = self.purchase_table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要查看的采购订单")
            return
        
        row = selected[0].row()
        order = self.purchase_orders[row]
        
        dialog = PurchaseDetailDialog(self.db_session, order)
        dialog.exec_()
    
    def filter_purchase_orders(self):
        self.load_purchase_orders()
    
    def add_supplier(self):
        dialog = SupplierEditDialog(self.db_session, self, None)
        if dialog.exec_() == QDialog.Accepted:
            self.load_suppliers()
            QMessageBox.information(self, "成功", "供应商添加成功!")
    
    def edit_supplier(self):
        selected = self.supplier_table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要编辑的供应商")
            return
        
        row = selected[0].row()
        supplier = self.suppliers[row]
        
        dialog = SupplierEditDialog(self.db_session, self, supplier)
        if dialog.exec_() == QDialog.Accepted:
            self.load_suppliers()
            QMessageBox.information(self, "成功", "供应商更新成功!")
    
    def delete_supplier(self):
        selected = self.supplier_table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要删除的供应商")
            return
        
        row = selected[0].row()
        supplier = self.suppliers[row]
        
        reply = QMessageBox.question(
            self, "确认", f"确定要删除供应商 {supplier.name} 吗？",
            QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                if self.controller.delete_supplier(supplier.id):
                    self.load_suppliers()
                    QMessageBox.information(self, "成功", "供应商已删除")
            except Exception as e:
                logger.error(f"删除供应商失败: {e}")
                QMessageBox.critical(self, "错误", f"删除失败: {str(e)}")
    
    def add_purchase_order(self):
        dialog = PurchaseOrderEditDialog(self.db_session, self, None)
        if dialog.exec_() == QDialog.Accepted:
            self.load_purchase_orders()
            QMessageBox.information(self, "成功", "采购订单创建成功!")
    
    def edit_purchase_order(self):
        selected = self.purchase_table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要编辑的订单")
            return
        
        row = selected[0].row()
        order = self.purchase_orders[row]
        
        if order.status not in ['待入库', '待退货']:
            QMessageBox.warning(self, "提示", "只能编辑待处理的订单")
            return
            
        dialog = PurchaseOrderEditDialog(self.db_session, self, purchase_order=order, order_type=getattr(order, 'order_type', '采购'))
        if dialog.exec_() == QDialog.Accepted:
            self.load_purchase_orders()
            QMessageBox.information(self, "成功", "订单更新成功!")

    def receive_purchase_order(self):
        selected = self.purchase_table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要入库的采购订单")
            return
        
        row = selected[0].row()
        order = self.purchase_orders[row]
        
        if order.status != "待入库":
            QMessageBox.warning(self, "提示", "该订单无法入库")
            return
        
        reply = QMessageBox.question(
            self, "确认", f"确定要对订单 {order.order_no} 入库吗？",
            QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                self.controller.receive_purchase_order(order.id, self.current_user.username)
                self.load_purchase_orders()
                QMessageBox.information(self, "成功", "入库完成!")
            except Exception as e:
                logger.error(f"入库失败: {e}")
                QMessageBox.critical(self, "错误", f"入库失败: {str(e)}")
    
    def return_purchase_order(self):
        selected = self.purchase_table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要退货的采购订单")
            return
        
        row = selected[0].row()
        order = self.purchase_orders[row]
        
        if order.status != "已完成":
            QMessageBox.warning(self, "提示", "只能对已完成的订单进行退货")
            return
            
        if getattr(order, 'order_type', '采购') == '退货':
             QMessageBox.warning(self, "提示", "不能对退货单进行退货")
             return

        dialog = PurchaseOrderEditDialog(self.db_session, self, order_type="退货", ref_order=order)
        if dialog.exec_() == QDialog.Accepted:
            self.load_purchase_orders()
            QMessageBox.information(self, "成功", "退货单创建成功!")


class SupplierEditDialog(QDialog):
    def __init__(self, db_session, parent, supplier=None):
        super().__init__(parent)
        self.db_session = db_session
        self.supplier = supplier
        self.controller = None
        self.init_ui()
        self.init_controller()
        
        if supplier:
            self.setWindowTitle("编辑供应商")
            self.load_supplier_data()
        else:
            self.setWindowTitle("新增供应商")
    
    def init_controller(self):
        try:
            with self.db_session() as db:
                self.controller = PurchaseController(db)
        except Exception as e:
            logger.error(f"初始化控制器失败: {e}")
    
    def init_ui(self):
        layout = QFormLayout()
        
        self.code_input = QLineEdit()
        self.name_input = QLineEdit()
        self.contact_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.address_input = QLineEdit()
        self.remark_input = QTextEdit()
        self.remark_input.setMaximumHeight(80)
        
        layout.addRow("供应商编码 *:", self.code_input)
        layout.addRow("供应商名称 *:", self.name_input)
        layout.addRow("联系人:", self.contact_input)
        layout.addRow("电话:", self.phone_input)
        layout.addRow("地址:", self.address_input)
        layout.addRow("备注:", self.remark_input)
        
        buttons = QHBoxLayout()
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.save_supplier)
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
    
    def load_supplier_data(self):
        self.code_input.setText(self.supplier.code)
        self.code_input.setReadOnly(True)
        self.name_input.setText(self.supplier.name)
        self.contact_input.setText(self.supplier.contact or "")
        self.phone_input.setText(self.supplier.phone or "")
        self.address_input.setText(self.supplier.address or "")
        self.remark_input.setText(self.supplier.remark or "")
    
    def save_supplier(self):
        code = self.code_input.text().strip()
        name = self.name_input.text().strip()
        
        if not code or not name:
            QMessageBox.warning(self, "提示", "请填写必填项")
            return
        
        try:
            data = {
                'code': code,
                'name': name,
                'contact': self.contact_input.text().strip() or None,
                'phone': self.phone_input.text().strip() or None,
                'address': self.address_input.text().strip() or None,
                'remark': self.remark_input.toPlainText().strip() or None
            }
            
            if self.supplier:
                self.controller.update_supplier(self.supplier.id, **data)
            else:
                self.controller.create_supplier(**data)
            
            self.accept()
        except Exception as e:
            logger.error(f"保存供应商失败: {e}")
            QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")


class PurchaseOrderEditDialog(QDialog):
    def __init__(self, db_session, parent, purchase_order=None, order_type="采购", ref_order=None):
        super().__init__(parent)
        self.db_session = db_session
        self.purchase_order = purchase_order
        self.order_type = order_type
        self.ref_order = ref_order
        self.controller = None
        self.product_controller = None
        self.selected_items = []
        self.suppliers = []
        self.products = []
        self.init_ui()
        self.init_controller()
        self.load_suppliers()
        self.load_products()
        
        if self.ref_order:
            self.load_ref_order_data()
        elif self.purchase_order:
            self.load_order_data()
    
    def init_controller(self):
        try:
            with self.db_session() as db:
                self.controller = PurchaseController(db)
                self.product_controller = ProductController(db)
        except Exception as e:
            logger.error(f"初始化控制器失败: {e}")
    
    def init_ui(self):
        if self.order_type == '退货':
             self.setWindowTitle("采购退货")
        else:
             self.setWindowTitle("新建采购订单")
        layout = QVBoxLayout()
        
        form_layout = QFormLayout()
        
        self.supplier_combo = QComboBox()
        form_layout.addRow("供应商 *:", self.supplier_combo)
        
        self.remark_input = QTextEdit()
        self.remark_input.setMaximumHeight(60)
        form_layout.addRow("备注:", self.remark_input)
        
        layout.addLayout(form_layout)
        
        layout.addWidget(QLabel("商品列表:"))
        
        item_toolbar = QHBoxLayout()
        add_item_btn = QPushButton("添加商品")
        add_item_btn.clicked.connect(self.add_item)
        remove_item_btn = QPushButton("删除商品")
        remove_item_btn.clicked.connect(self.remove_item)
        item_toolbar.addWidget(add_item_btn)
        item_toolbar.addWidget(remove_item_btn)
        item_toolbar.addStretch()
        
        layout.addLayout(item_toolbar)
        
        self.item_table = QTableWidget()
        self.item_table.setColumnCount(5)
        self.item_table.setHorizontalHeaderLabels(["商品编码", "商品名称", "数量", "单价", "小计"])
        self.item_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.item_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.item_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.item_table)
        
        total_layout = QHBoxLayout()
        self.total_label = QLabel("总金额: ¥0.00")
        self.total_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #e74c3c;")
        total_layout.addStretch()
        total_layout.addWidget(self.total_label)
        
        layout.addLayout(total_layout)
        
        buttons = QHBoxLayout()
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.save_purchase_order)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        buttons.addStretch()
        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)
        
        layout.addLayout(buttons)
        
        self.setLayout(layout)
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)
    
    def load_suppliers(self):
        try:
            with self.db_session() as db:
                self.suppliers = self.controller.list_suppliers()
            
            self.supplier_combo.clear()
            for supplier in self.suppliers:
                self.supplier_combo.addItem(f"{supplier.code} - {supplier.name}", supplier.id)
        except Exception as e:
            logger.error(f"加载供应商失败: {e}")
    
    def load_products(self):
        try:
            with self.db_session() as db:
                controller = ProductController(db)
                product_instances = controller.list_products()
                # 创建数据传输对象，避免会话依赖
                class ProductDTO:
                    def __init__(self, product):
                        self.id = product.id
                        self.code = product.code
                        self.name = product.name
                        self.price_cost = product.price_cost
                        self.price_sale = product.price_sale
                        self.stock_quantity = product.stock_quantity
                        self.status = product.status
                        # 复制其他可能需要的属性
                        for attr in ['barcode', 'category_id', 'brand', 'specification', 'min_stock', 'max_stock', 'description']:
                            if hasattr(product, attr):
                                setattr(self, attr, getattr(product, attr))
                # 转换为DTO列表
                self.products = [ProductDTO(p) for p in product_instances]
        except Exception as e:
            logger.error(f"加载商品失败: {e}")

    def load_order_data(self):
        if not self.purchase_order:
            return
            
        # 设置供应商
        index = self.supplier_combo.findData(self.purchase_order.supplier_id)
        if index >= 0:
            self.supplier_combo.setCurrentIndex(index)
        
        # 设置备注
        self.remark_input.setText(self.purchase_order.remark or "")
        
        # 加载商品
        self.selected_items = []
        for item in self.purchase_order.items:
             product = next((p for p in self.products if p.id == item.product_id), None)
             if product:
                 self.selected_items.append({
                     'product_id': item.product_id,
                     'product': product,
                     'quantity': item.quantity, 
                     'price': item.price,
                     'amount': item.amount
                 })
        self.refresh_item_table()

    def load_ref_order_data(self):
        if not self.ref_order:
            return
            
        # 设置供应商
        index = self.supplier_combo.findData(self.ref_order.supplier_id)
        if index >= 0:
            self.supplier_combo.setCurrentIndex(index)
            self.supplier_combo.setEnabled(False) # 锁定供应商
            
        # 加载商品
        self.selected_items = []
        for item in self.ref_order.items:
             product = next((p for p in self.products if p.id == item.product_id), None)
             if product:
                 self.selected_items.append({
                     'product_id': item.product_id,
                     'product': product,
                     'quantity': item.quantity, 
                     'price': item.price,
                     'amount': item.amount
                 })
        self.refresh_item_table()
    
    def add_item(self):
        try:
            if not self.products:
                QMessageBox.warning(self, "提示", "商品列表为空，请先加载商品")
                self.load_products()
                if not self.products:
                    QMessageBox.critical(self, "错误", "商品列表加载失败")
                    return
            
            dialog = PurchaseItemDialog(self, self.products)
            if dialog.exec_() == QDialog.Accepted and dialog.selected_product:
                item = {
                    'product_id': dialog.selected_product.id,
                    'product': dialog.selected_product,
                    'quantity': dialog.quantity,
                    'price': dialog.price,
                    'amount': dialog.quantity * dialog.price
                }
                self.selected_items.append(item)
                self.refresh_item_table()
                logger.info(f"添加采购商品: {dialog.selected_product.code} - {dialog.selected_product.name}, 数量: {dialog.quantity}, 单价: {dialog.price}")
        except Exception as e:
            logger.error(f"添加商品失败: {e}")
            QMessageBox.critical(self, "错误", f"添加商品失败: {str(e)}")
    
    def remove_item(self):
        selected = self.item_table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要删除的商品")
            return
        
        row = selected[0].row()
        del self.selected_items[row]
        self.refresh_item_table()
    
    def refresh_item_table(self):
        self.item_table.setRowCount(len(self.selected_items))
        
        total = 0.0
        for row, item in enumerate(self.selected_items):
            self.item_table.setItem(row, 0, QTableWidgetItem(item['product'].code))
            self.item_table.setItem(row, 1, QTableWidgetItem(item['product'].name))
            
            qty_item = QTableWidgetItem(str(item['quantity']))
            qty_item.setData(Qt.UserRole, item)
            self.item_table.setItem(row, 2, qty_item)
            
            self.item_table.setItem(row, 3, QTableWidgetItem(f"¥{item['price']:.2f}"))
            self.item_table.setItem(row, 4, QTableWidgetItem(f"¥{item['amount']:.2f}"))
            
            total += item['amount']
            
            for col in range(5):
                self.item_table.item(row, col).setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        
        self.total_label.setText(f"总金额: ¥{total:.2f}")
    
    def save_purchase_order(self):
        if self.supplier_combo.currentData() is None:
            QMessageBox.warning(self, "提示", "请选择供应商")
            return
        
        if len(self.selected_items) == 0:
            QMessageBox.warning(self, "提示", "请添加商品")
            return
        
        try:
            supplier_id = self.supplier_combo.currentData()
            items = [
                {
                    'product_id': item['product_id'],
                    'quantity': item['quantity'],
                    'price': item['price']
                }
                for item in self.selected_items
            ]
            
            if self.purchase_order:
                self.controller.update_purchase_order_with_items(
                    purchase_id=self.purchase_order.id,
                    supplier_id=supplier_id,
                    items=items,
                    remark=self.remark_input.toPlainText().strip(),
                    operator=self.parent().current_user.username
                )
            else:
                self.controller.create_purchase_order(
                    supplier_id=supplier_id,
                    items=items,
                    remark=self.remark_input.toPlainText().strip(),
                    order_type=self.order_type,
                    ref_order_no=self.ref_order.order_no if self.ref_order else None,
                    operator=self.parent().current_user.username
                )
            
            self.accept()
        except Exception as e:
            logger.error(f"保存采购订单失败: {e}")
            QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")


class PurchaseItemDialog(QDialog):
    def __init__(self, parent, products):
        super().__init__(parent)
        self.products = products
        self.selected_product = None
        self.quantity = 1
        self.price = 0.0
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("添加商品")
        layout = QFormLayout()
        
        self.product_combo = QComboBox()
        for product in self.products:
            self.product_combo.addItem(f"{product.code} - {product.name}", product)
        self.product_combo.currentIndexChanged.connect(self.on_product_changed)
        
        self.quantity_spin = QDoubleSpinBox()
        self.quantity_spin.setRange(0.01, 999999)
        self.quantity_spin.setDecimals(2)
        self.quantity_spin.setValue(1.00)
        self.quantity_spin.valueChanged.connect(self.calculate_amount)
        
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0, 999999)
        self.price_spin.setDecimals(2)
        self.price_spin.valueChanged.connect(self.calculate_amount)
        
        self.amount_label = QLabel("¥0.00")
        self.amount_label.setStyleSheet("font-weight: bold; color: #e74c3c;")
        
        layout.addRow("商品 *:", self.product_combo)
        layout.addRow("数量 *:", self.quantity_spin)
        layout.addRow("单价 *:", self.price_spin)
        layout.addRow("小计:", self.amount_label)
        
        buttons = QHBoxLayout()
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
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
        
        if self.products:
            self.on_product_changed(0)
    
    def on_product_changed(self, index):
        product = self.product_combo.currentData()
        if product:
            self.price_spin.setValue(product.price_cost or 0.0)
    
    def calculate_amount(self):
        self.quantity = self.quantity_spin.value()
        self.price = self.price_spin.value()
        amount = self.quantity * self.price
        self.amount_label.setText(f"¥{amount:.2f}")
    
    def accept(self):
        try:
            self.selected_product = self.product_combo.currentData()
            if not self.selected_product:
                QMessageBox.warning(self, "提示", "请选择商品")
                return
            
            # 确保selected_product有必要的属性
            if not hasattr(self.selected_product, 'id'):
                QMessageBox.warning(self, "提示", "商品数据无效")
                return
            
            self.quantity = self.quantity_spin.value()
            if self.quantity <= 0:
                QMessageBox.warning(self, "提示", "数量必须大于0")
                return
            
            self.price = self.price_spin.value()
            if self.price <= 0:
                QMessageBox.warning(self, "提示", "单价必须大于0")
                return
            
            # 确保金额计算正确
            self.calculate_amount()
            
            super().accept()
        except Exception as e:
            logger.error(f"确认添加商品失败: {e}")
            QMessageBox.critical(self, "错误", f"确认添加商品失败: {str(e)}")


class PurchaseDetailDialog(QDialog):
    def __init__(self, db_session, purchase_order):
        super().__init__()
        self.db_session = db_session
        self.purchase_order = purchase_order
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle(f"采购订单详情 - {self.purchase_order.order_no}")
        layout = QVBoxLayout()
        
        # 订单信息
        info_layout = QFormLayout()
        info_layout.addRow("订单号:", QLabel(self.purchase_order.order_no))
        info_layout.addRow("供应商:", QLabel(self.purchase_order.supplier.name if self.purchase_order.supplier else ""))
        info_layout.addRow("总金额:", QLabel(f"¥{self.purchase_order.total_amount:.2f}"))
        info_layout.addRow("状态:", QLabel(self.purchase_order.status))
        info_layout.addRow("创建时间:", QLabel(self.purchase_order.create_time.strftime("%Y-%m-%d %H:%M")))
        if self.purchase_order.finish_time:
            info_layout.addRow("完成时间:", QLabel(self.purchase_order.finish_time.strftime("%Y-%m-%d %H:%M")))
        if self.purchase_order.remark:
            info_layout.addRow("备注:", QLabel(self.purchase_order.remark))
        
        layout.addLayout(info_layout)
        layout.addWidget(QLabel("<hr>", alignment=Qt.AlignCenter))
        
        # 商品列表
        layout.addWidget(QLabel("商品列表:"))
        
        self.item_table = QTableWidget()
        self.item_table.setColumnCount(5)
        self.item_table.setHorizontalHeaderLabels(["商品编码", "商品名称", "数量", "单价", "小计"])
        self.item_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.item_table.setAlternatingRowColors(True)
        
        # 填充商品数据
        self.item_table.setRowCount(len(self.purchase_order.items))
        for row, item in enumerate(self.purchase_order.items):
            product = item.product
            self.item_table.setItem(row, 0, QTableWidgetItem(product.code if product else ""))
            self.item_table.setItem(row, 1, QTableWidgetItem(product.name if product else ""))
            self.item_table.setItem(row, 2, QTableWidgetItem(str(item.quantity)))
            self.item_table.setItem(row, 3, QTableWidgetItem(f"¥{item.price:.2f}"))
            self.item_table.setItem(row, 4, QTableWidgetItem(f"¥{item.amount:.2f}"))
            
            for col in range(5):
                self.item_table.item(row, col).setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        
        layout.addWidget(self.item_table)
        
        # 按钮
        buttons = QHBoxLayout()
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.reject)
        buttons.addStretch()
        buttons.addWidget(close_btn)
        
        layout.addLayout(buttons)
        self.setLayout(layout)
        self.setMinimumWidth(800)
        self.setMinimumHeight(400)
