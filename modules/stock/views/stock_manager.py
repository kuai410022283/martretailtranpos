from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView,
    QLineEdit, QLabel, QMessageBox, QDialog,
    QFormLayout, QTabWidget, QCheckBox, QDoubleSpinBox,
    QSpinBox, QDateEdit, QComboBox, QGridLayout
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtChart import QChart, QChartView, QPieSeries, QPieSlice, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis
from PyQt5.QtGui import QPainter, QColor, QFont
from sqlalchemy.orm import Session
from shared.models.stock_log import StockLog
from shared.models.product import Product
from modules.stock.controllers import StockController
from modules.product.controllers import ProductController
from core.logger import logger
from datetime import datetime

class StockManager(QWidget):
    def __init__(self, db_session: Session, current_user):
        super().__init__()
        self.db_session = db_session
        self.current_user = current_user
        self.stock_controller = None
        self.product_controller = None
        self.init_ui()
        self.init_controllers()
        self.load_stock()
        self.load_stock_logs()
    
    def init_controllers(self):
        # 控制器将在需要时创建，确保使用新的数据库会话
        pass
    
    def init_ui(self):
        self.setWindowTitle("库存管理")
        
        # 订阅销售完成事件，自动刷新数据
        from core.event_bus import subscribe_event
        subscribe_event("sale_completed", self.on_sale_completed)
        
        layout = QVBoxLayout()
        
        self.tab_widget = QTabWidget()
        
        self.stock_tab = QWidget()
        self.stock_products = []
        self.init_stock_tab()
        
        self.log_tab = QWidget()
        self.stock_logs = []
        self.init_log_tab()
        
        self.check_tab = QWidget()
        self.init_check_tab()
        
        self.tab_widget.addTab(self.stock_tab, "库存查询")
        self.tab_widget.addTab(self.log_tab, "库存变动")
        self.tab_widget.addTab(self.check_tab, "库存盘点")
        
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)
    
    def init_stock_tab(self):
        layout = QVBoxLayout()
        
        toolbar = QHBoxLayout()
        self.stock_search = QLineEdit()
        self.stock_search.setPlaceholderText("搜索商品...")
        self.stock_search.textChanged.connect(self.filter_stock)
        
        self.low_stock_check = QCheckBox("只看库存预警")
        self.low_stock_check.toggled.connect(self.filter_stock)
        
        adjust_btn = QPushButton("库存调整")
        adjust_btn.clicked.connect(self.adjust_stock)
        
        check_btn = QPushButton("库存盘点")
        check_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(2))
        
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.load_stock)
        
        toolbar.addWidget(QLabel("搜索:"))
        toolbar.addWidget(self.stock_search)
        toolbar.addWidget(self.low_stock_check)
        toolbar.addStretch()
        toolbar.addWidget(adjust_btn)
        toolbar.addWidget(check_btn)
        toolbar.addWidget(refresh_btn)
        
        # 库存概览区域
        overview_layout = QGridLayout()
        overview_layout.setContentsMargins(10, 10, 10, 10)
        
        # 库存状态卡片
        self.total_products_card = QWidget()
        self.total_products_card.setStyleSheet("QWidget { background-color: #e6f7ff; border-radius: 8px; padding: 15px; }")
        total_layout = QVBoxLayout()
        total_label = QLabel("商品总数")
        total_label.setStyleSheet("font-size: 14px; color: #1890ff;")
        self.total_products_value = QLabel("0")
        self.total_products_value.setStyleSheet("font-size: 24px; font-weight: bold; color: #1890ff;")
        total_layout.addWidget(total_label)
        total_layout.addWidget(self.total_products_value)
        self.total_products_card.setLayout(total_layout)
        
        self.low_stock_card = QWidget()
        self.low_stock_card.setStyleSheet("QWidget { background-color: #fff1f0; border-radius: 8px; padding: 15px; }")
        low_layout = QVBoxLayout()
        low_label = QLabel("库存不足")
        low_label.setStyleSheet("font-size: 14px; color: #f5222d;")
        self.low_stock_value = QLabel("0")
        self.low_stock_value.setStyleSheet("font-size: 24px; font-weight: bold; color: #f5222d;")
        low_layout.addWidget(low_label)
        low_layout.addWidget(self.low_stock_value)
        self.low_stock_card.setLayout(low_layout)
        
        self.high_stock_card = QWidget()
        self.high_stock_card.setStyleSheet("QWidget { background-color: #f6ffed; border-radius: 8px; padding: 15px; }")
        high_layout = QVBoxLayout()
        high_label = QLabel("库存过高")
        high_label.setStyleSheet("font-size: 14px; color: #52c41a;")
        self.high_stock_value = QLabel("0")
        self.high_stock_value.setStyleSheet("font-size: 24px; font-weight: bold; color: #52c41a;")
        high_layout.addWidget(high_label)
        high_layout.addWidget(self.high_stock_value)
        self.high_stock_card.setLayout(high_layout)
        
        self.normal_stock_card = QWidget()
        self.normal_stock_card.setStyleSheet("QWidget { background-color: #f0f5ff; border-radius: 8px; padding: 15px; }")
        normal_layout = QVBoxLayout()
        normal_label = QLabel("库存正常")
        normal_label.setStyleSheet("font-size: 14px; color: #722ed1;")
        self.normal_stock_value = QLabel("0")
        self.normal_stock_value.setStyleSheet("font-size: 24px; font-weight: bold; color: #722ed1;")
        normal_layout.addWidget(normal_label)
        normal_layout.addWidget(self.normal_stock_value)
        self.normal_stock_card.setLayout(normal_layout)
        
        overview_layout.addWidget(self.total_products_card, 0, 0)
        overview_layout.addWidget(self.low_stock_card, 0, 1)
        overview_layout.addWidget(self.high_stock_card, 0, 2)
        overview_layout.addWidget(self.normal_stock_card, 0, 3)
        
        # 库存状态图表
        chart_layout = QHBoxLayout()
        
        # 库存状态分布饼图
        self.status_chart = QChart()
        self.status_chart.setAnimationOptions(QChart.SeriesAnimations)
        self.status_chart.setTitle("库存状态分布")
        self.status_chart_view = QChartView(self.status_chart)
        self.status_chart_view.setRenderHint(QPainter.Antialiasing)
        self.status_chart_view.setMinimumHeight(200)
        self.status_chart_view.setMinimumWidth(300)
        
        # 库存变动趋势图
        self.trend_chart = QChart()
        self.trend_chart.setAnimationOptions(QChart.SeriesAnimations)
        self.trend_chart.setTitle("近期库存变动")
        self.trend_chart_view = QChartView(self.trend_chart)
        self.trend_chart_view.setRenderHint(QPainter.Antialiasing)
        self.trend_chart_view.setMinimumHeight(200)
        self.trend_chart_view.setMinimumWidth(300)
        
        chart_layout.addWidget(self.status_chart_view, 1)
        chart_layout.addWidget(self.trend_chart_view, 1)
        
        # 库存商品列表
        self.stock_table = QTableWidget()
        self.stock_table.setColumnCount(9)
        self.stock_table.setHorizontalHeaderLabels([
            "商品编码", "商品名称", "分类", "品牌", 
            "库存数量", "最低库存", "最高库存", "状态", "创建时间"])
        self.stock_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.stock_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.stock_table.setAlternatingRowColors(True)
        
        layout.addLayout(toolbar)
        layout.addLayout(overview_layout)
        layout.addLayout(chart_layout)
        layout.addWidget(self.stock_table)
        self.stock_tab.setLayout(layout)
    
    def init_log_tab(self):
        layout = QVBoxLayout()
        
        toolbar = QHBoxLayout()
        self.log_type = QLabel("类型:")
        self.log_type_combo = QComboBox()
        self.log_type_combo.addItem("全部", None)
        self.log_type_combo.addItem("入库", "入库")
        self.log_type_combo.addItem("出库", "出库")
        self.log_type_combo.addItem("盘点", "盘点")
        self.log_type_combo.currentIndexChanged.connect(self.filter_stock_logs)
        
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.load_stock_logs)
        
        toolbar.addWidget(self.log_type)
        toolbar.addWidget(self.log_type_combo)
        toolbar.addStretch()
        toolbar.addWidget(refresh_btn)
        
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(7)
        self.log_table.setHorizontalHeaderLabels([
            "商品", "类型", "变动数量", "关联单号", "操作员", "备注", "时间"])
        self.log_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.log_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.log_table.setAlternatingRowColors(True)
        
        layout.addLayout(toolbar)
        layout.addWidget(self.log_table)
        self.log_tab.setLayout(layout)
    
    def init_check_tab(self):
        layout = QVBoxLayout()
        
        toolbar = QHBoxLayout()
        start_check_btn = QPushButton("开始盘点")
        start_check_btn.clicked.connect(self.start_stock_check)
        
        finish_check_btn = QPushButton("完成盘点")
        finish_check_btn.clicked.connect(self.finish_stock_check)
        
        export_btn = QPushButton("导出盘点表")
        export_btn.clicked.connect(self.export_check_report)
        
        toolbar.addWidget(start_check_btn)
        toolbar.addWidget(finish_check_btn)
        toolbar.addStretch()
        toolbar.addWidget(export_btn)
        
        layout.addLayout(toolbar)
        
        self.check_info_label = QLabel("点击\"开始盘点\"创建新的盘点任务")
        self.check_info_label.setStyleSheet("color: #2c3e50; font-weight: bold; padding: 10px;")
        layout.addWidget(self.check_info_label)
        
        self.check_table = QTableWidget()
        self.check_table.setColumnCount(6)
        self.check_table.setHorizontalHeaderLabels([
            "商品编码", "商品名称", "系统库存", "实际库存", "差异数量", "状态"])
        self.check_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.check_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.check_table.setAlternatingRowColors(True)
        self.check_table.itemDoubleClicked.connect(self.edit_actual_quantity)
        
        layout.addWidget(self.check_table)
        self.check_tab.setLayout(layout)
        
        self.check_items = []
        self.check_in_progress = False
    
    def load_stock(self):
        try:
            with self.db_session() as db:
                product_controller = ProductController(db)
                keyword = self.stock_search.text().strip()
                low_stock_only = self.low_stock_check.isChecked()
                
                # 加载所有商品用于统计
                all_products = product_controller.list_products()
                
                # 过滤商品
                self.stock_products = product_controller.list_products(
                    keyword=keyword if keyword else None
                )
                
                if low_stock_only:
                    self.stock_products = [
                        p for p in self.stock_products 
                        if p.stock_quantity <= p.min_stock
                    ]
                
                # 统计库存状态
                total_count = len(all_products)
                low_stock_count = len([p for p in all_products if p.stock_quantity <= p.min_stock])
                high_stock_count = len([p for p in all_products if p.stock_quantity >= p.max_stock])
                normal_stock_count = total_count - low_stock_count - high_stock_count
                
                # 更新库存状态卡片
                self.total_products_value.setText(str(total_count))
                self.low_stock_value.setText(str(low_stock_count))
                self.high_stock_value.setText(str(high_stock_count))
                self.normal_stock_value.setText(str(normal_stock_count))
                
                # 更新库存状态分布饼图
                self.update_status_chart(low_stock_count, high_stock_count, normal_stock_count)
                
                # 更新库存变动趋势图
                self.update_trend_chart()
                
                # 更新库存商品列表
                self.stock_table.setRowCount(len(self.stock_products))
                
                for row, product in enumerate(self.stock_products):
                    self.stock_table.setItem(row, 0, QTableWidgetItem(product.code))
                    self.stock_table.setItem(row, 1, QTableWidgetItem(product.name))
                    
                    category_name = product.category.name if product.category else ""
                    self.stock_table.setItem(row, 2, QTableWidgetItem(category_name))
                    
                    self.stock_table.setItem(row, 3, QTableWidgetItem(product.brand or ""))
                    
                    stock_item = QTableWidgetItem(f"{product.stock_quantity:.2f}")
                    if product.stock_quantity <= product.min_stock:
                        stock_item.setForeground(Qt.red)
                    elif product.stock_quantity >= product.max_stock:
                        stock_item.setForeground(Qt.green)
                    self.stock_table.setItem(row, 4, stock_item)
                    
                    self.stock_table.setItem(row, 5, QTableWidgetItem(f"{product.min_stock:.2f}"))
                    self.stock_table.setItem(row, 6, QTableWidgetItem(f"{product.max_stock:.2f}"))
                    
                    if product.stock_quantity <= product.min_stock:
                        status = "库存不足"
                    elif product.stock_quantity >= product.max_stock:
                        status = "库存过高"
                    else:
                        status = "正常"
                    self.stock_table.setItem(row, 7, QTableWidgetItem(status))
                    
                    self.stock_table.setItem(row, 8, QTableWidgetItem(
                        product.create_time.strftime("%Y-%m-%d")))
                    
                    for col in range(9):
                        self.stock_table.item(row, col).setFlags(
                            Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        except Exception as e:
            logger.error(f"加载库存失败: {e}")
    
    def update_status_chart(self, low_count, high_count, normal_count):
        """更新库存状态分布饼图"""
        self.status_chart.removeAllSeries()
        
        series = QPieSeries()
        
        if low_count > 0:
            series.append(f"库存不足 ({low_count})", low_count)
        
        if high_count > 0:
            series.append(f"库存过高 ({high_count})", high_count)
        
        if normal_count > 0:
            series.append(f"库存正常 ({normal_count})", normal_count)
        
        # 设置颜色
        slices = series.slices()
        if slices:
            if low_count > 0:
                slices[0].setBrush(QColor(245, 34, 45))
            if high_count > 0:
                if low_count > 0:
                    slices[1].setBrush(QColor(82, 196, 26))
                else:
                    slices[0].setBrush(QColor(82, 196, 26))
            if normal_count > 0:
                if low_count > 0 and high_count > 0:
                    slices[2].setBrush(QColor(114, 46, 209))
                elif low_count > 0 or high_count > 0:
                    slices[1].setBrush(QColor(114, 46, 209))
                else:
                    slices[0].setBrush(QColor(114, 46, 209))
        
        self.status_chart.addSeries(series)
    
    def update_trend_chart(self):
        """更新库存变动趋势图"""
        self.trend_chart.removeAllSeries()
        
        # 移除旧的坐标轴，防止叠加
        for axis in self.trend_chart.axes():
            self.trend_chart.removeAxis(axis)
        
        # 获取最近7天的库存变动数据
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        try:
            # 在会话内部处理所有数据操作并提取所需数据
            daily_changes = {}
            with self.db_session() as db:
                controller = StockController(db)
                logs = controller.get_stock_logs(start_date=start_date, end_date=end_date)
                
                # 按日期分组统计
                for log in logs:
                    date_key = log.create_time.strftime('%Y-%m-%d')
                    if date_key not in daily_changes:
                        daily_changes[date_key] = 0
                    daily_changes[date_key] += log.quantity
            
            # 创建日期列表
            dates = []
            changes = []
            current = start_date
            while current <= end_date:
                date_key = current.strftime('%Y-%m-%d')
                dates.append(date_key)
                changes.append(daily_changes.get(date_key, 0))
                current += timedelta(days=1)
            
            # 创建条形系列
            series = QBarSeries()
            set_data = QBarSet("库存变动")
            set_data.append(changes)
            series.append(set_data)
            
            # 添加到图表
            self.trend_chart.addSeries(series)
            
            # 创建轴
            axis_x = QBarCategoryAxis()
            axis_x.append(dates)
            axis_x.setLabelsAngle(-45)
            
            axis_y = QValueAxis()
            axis_y.setTitleText("变动数量")
            # 根据数据自动调整范围，或者设置固定范围
            min_val = min(changes) if changes else 0
            max_val = max(changes) if changes else 0
            if min_val > 0: min_val = 0
            if max_val < 0: max_val = 0
            
            # 稍微扩大一点范围
            range_val = max_val - min_val
            if range_val == 0:
                range_val = 10
            
            axis_y.setRange(min_val - range_val * 0.1, max_val + range_val * 0.1)
            
            self.trend_chart.setAxisX(axis_x, series)
            self.trend_chart.setAxisY(axis_y, series)
            
        except Exception as e:
            logger.error(f"更新库存趋势图表失败: {e}")
    
    def filter_stock(self):
        self.load_stock()
    
    def on_sale_completed(self, **kwargs):
        """当销售完成时触发，刷新库存数据"""
        logger.info("收到销售完成事件，正在刷新库存数据...")
        self.load_stock()
        self.load_stock_logs()
    
    def load_stock_logs(self):
        try:
            with self.db_session() as db:
                controller = StockController(db)
                log_type = self.log_type_combo.currentData()
                self.stock_logs = controller.list_stock_logs(log_type=log_type)
                self.log_table.setRowCount(len(self.stock_logs))
                
                for row, log in enumerate(self.stock_logs):
                    product_name = log.product.name if log.product else ""
                    self.log_table.setItem(row, 0, QTableWidgetItem(product_name))
                    self.log_table.setItem(row, 1, QTableWidgetItem(log.type))
                    self.log_table.setItem(row, 2, QTableWidgetItem(f"{log.quantity:+.2f}"))
                    self.log_table.setItem(row, 3, QTableWidgetItem(log.related_order_no or ""))
                    self.log_table.setItem(row, 4, QTableWidgetItem(log.operator or ""))
                    self.log_table.setItem(row, 5, QTableWidgetItem(log.remark or ""))
                    self.log_table.setItem(row, 6, QTableWidgetItem(
                        log.create_time.strftime("%Y-%m-%d %H:%M")))
                    
                    for col in range(7):
                        self.log_table.item(row, col).setFlags(
                            Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        except Exception as e:
            logger.error(f"加载库存日志失败: {e}")
    
    def filter_stock_logs(self):
        self.load_stock_logs()
    
    def adjust_stock(self):
        selected = self.stock_table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要调整的商品")
            return
        
        row = selected[0].row()
        product = self.stock_products[row]
        
        dialog = StockAdjustDialog(self.db_session, self, product)
        if dialog.exec_() == QDialog.Accepted:
            self.load_stock()
            self.load_stock_logs()
            QMessageBox.information(self, "成功", "库存调整完成!")
    
    def start_stock_check(self):
        if self.check_in_progress:
            QMessageBox.warning(self, "提示", "盘点进行中，请先完成或取消当前盘点")
            return
        
        try:
            self.check_in_progress = True
            self.check_items = []
            
            with self.db_session() as db:
                product_controller = ProductController(db)
                products = product_controller.list_products()
                
                for product in products:
                    self.check_items.append({
                        'product_id': product.id,
                        'code': product.code,
                        'name': product.name,
                        'system_qty': product.stock_quantity,
                        'actual_qty': None,
                        'status': '未盘点'
                    })
            
            self.check_info_label.setText(
                f"盘点进行中 - 共 {len(self.check_items)} 个商品 | 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.refresh_check_table()
            
        except Exception as e:
            logger.error(f"开始盘点失败: {e}")
            QMessageBox.critical(self, "错误", f"开始盘点失败: {str(e)}")
    
    def refresh_check_table(self):
        self.check_table.setRowCount(len(self.check_items))
        
        for row, item in enumerate(self.check_items):
            self.check_table.setItem(row, 0, QTableWidgetItem(item['code']))
            self.check_table.setItem(row, 1, QTableWidgetItem(item['name']))
            self.check_table.setItem(row, 2, QTableWidgetItem(f"{item['system_qty']:.0f}"))
            
            actual_qty_str = f"{item['actual_qty']:.0f}" if item['actual_qty'] is not None else ""
            self.check_table.setItem(row, 3, QTableWidgetItem(actual_qty_str))
            
            diff_qty = item['actual_qty'] - item['system_qty'] if item['actual_qty'] is not None else 0
            diff_str = f"{diff_qty:+.0f}" if item['actual_qty'] is not None else ""
            diff_item = QTableWidgetItem(diff_str)
            if diff_qty > 0:
                diff_item.setForeground(Qt.green)
            elif diff_qty < 0:
                diff_item.setForeground(Qt.red)
            self.check_table.setItem(row, 4, diff_item)
            
            status_item = QTableWidgetItem(item['status'])
            if item['status'] == '已盘点':
                status_item.setForeground(Qt.darkGreen)
            elif item['status'] == '有差异':
                status_item.setForeground(Qt.red)
            self.check_table.setItem(row, 5, status_item)
            
            for col in range(6):
                self.check_table.item(row, col).setFlags(
                    Qt.ItemIsSelectable | Qt.ItemIsEnabled)
    
    def edit_actual_quantity(self, item):
        if not self.check_in_progress:
            return
        
        row = item.row()
        check_item = self.check_items[row]
        
        dialog = StockCheckEditDialog(self, check_item)
        if dialog.exec_() == QDialog.Accepted:
            check_item['actual_qty'] = dialog.actual_qty
            
            if check_item['actual_qty'] is not None:
                diff = check_item['actual_qty'] - check_item['system_qty']
                if diff != 0:
                    check_item['status'] = '有差异'
                else:
                    check_item['status'] = '已盘点'
            
            self.refresh_check_table()
    
    def finish_stock_check(self):
        if not self.check_in_progress:
            QMessageBox.warning(self, "提示", "没有进行中的盘点")
            return
        
        unchecked_count = len([item for item in self.check_items if item['status'] == '未盘点'])
        if unchecked_count > 0:
            reply = QMessageBox.question(
                self, "确认",
                f"还有 {unchecked_count} 个商品未盘点，确定要完成盘点吗？",
                QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                return
        
        try:
            with self.db_session() as db:
                controller = StockController(db)
                
                for item in self.check_items:
                    if item['actual_qty'] is None:
                        continue
                    
                    diff = item['actual_qty'] - item['system_qty']
                    if diff == 0:
                        continue
                    
                    controller.adjust_stock(
                        product_id=item['product_id'],
                        quantity=diff,
                        type='盘点',
                        operator=self.current_user.username,
                        remark=f'盘点调整，系统库存: {item["system_qty"]:.0f}，实际库存: {item["actual_qty"]:.0f}'
                    )
                
                db.commit()
            
            self.check_in_progress = False
            self.check_items = []
            self.check_info_label.setText("点击\"开始盘点\"创建新的盘点任务")
            self.refresh_check_table()
            self.load_stock()
            self.load_stock_logs()
            
            QMessageBox.information(self, "成功", "库存盘点完成!")
        
        except Exception as e:
            logger.error(f"完成盘点失败: {e}")
            QMessageBox.critical(self, "错误", f"完成盘点失败: {str(e)}")
    
    def export_check_report(self):
        QMessageBox.information(self, "提示", "导出盘点表功能开发中...")


class StockAdjustDialog(QDialog):
    def __init__(self, db_session, parent, product):
        super().__init__(parent)
        self.db_session = db_session
        self.product = product
        self.controller = None
        self.init_ui()
        self.init_controller()
    
    def init_controller(self):
        try:
            with self.db_session() as db:
                self.controller = StockController(db)
        except Exception as e:
            logger.error(f"初始化控制器失败: {e}")
    
    def init_ui(self):
        self.setWindowTitle("库存调整")
        layout = QFormLayout()
        
        self.code_label = QLabel(self.product.code)
        self.name_label = QLabel(self.product.name)
        self.current_stock_label = QLabel(f"{self.product.stock_quantity:.2f}")
        
        self.adjust_type_combo = QComboBox()
        self.adjust_type_combo.addItem("增加库存", 1)
        self.adjust_type_combo.addItem("减少库存", -1)
        
        self.quantity_spin = QDoubleSpinBox()
        self.quantity_spin.setRange(0.01, 999999)
        self.quantity_spin.setDecimals(2)
        self.quantity_spin.setValue(1.00)
        
        self.remark_input = QLineEdit()
        
        layout.addRow("商品编码:", self.code_label)
        layout.addRow("商品名称:", self.name_label)
        layout.addRow("当前库存:", self.current_stock_label)
        layout.addRow("调整类型:", self.adjust_type_combo)
        layout.addRow("调整数量:", self.quantity_spin)
        layout.addRow("备注:", self.remark_input)
        
        buttons = QHBoxLayout()
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.save_adjust)
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
    
    def save_adjust(self):
        adjust_type = self.adjust_type_combo.currentData()
        quantity = self.quantity_spin.value() * adjust_type
        
        try:
            self.controller.adjust_stock(
                product_id=self.product.id,
                quantity=quantity,
                type='调整',
                operator=self.parent().current_user.username,
                remark=self.remark_input.text().strip() or None
            )
            self.accept()
        except Exception as e:
            logger.error(f"库存调整失败: {e}")
            QMessageBox.critical(self, "错误", f"调整失败: {str(e)}")


class StockCheckEditDialog(QDialog):
    def __init__(self, parent, check_item):
        super().__init__(parent)
        self.check_item = check_item
        self.actual_qty = check_item['actual_qty']
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("录入实际库存")
        layout = QFormLayout()
        
        self.code_label = QLabel(self.check_item['code'])
        self.name_label = QLabel(self.check_item['name'])
        self.system_qty_label = QLabel(f"{self.check_item['system_qty']:.2f}")
        
        self.actual_qty_spin = QDoubleSpinBox()
        self.actual_qty_spin.setRange(0, 999999)
        self.actual_qty_spin.setDecimals(2)
        if self.actual_qty is not None:
            self.actual_qty_spin.setValue(self.actual_qty)
        
        layout.addRow("商品编码:", self.code_label)
        layout.addRow("商品名称:", self.name_label)
        layout.addRow("系统库存:", self.system_qty_label)
        layout.addRow("实际库存:", self.actual_qty_spin)
        
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
    
    def accept(self):
        self.actual_qty = self.actual_qty_spin.value()
        super().accept()
