from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView,
    QLabel, QMessageBox, QTabWidget, QDateEdit, QComboBox
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis
from PyQt5.QtGui import QPainter, QPen, QColor
from sqlalchemy.orm import Session
from modules.sale.controllers import SaleController
from core.logger import logger

class SaleManager(QWidget):
    def __init__(self, db_session: Session, current_user):
        super().__init__()
        self.db_session = db_session
        self.current_user = current_user
        self.init_ui()
        self.load_sales()
    
    def init_ui(self):
        self.setWindowTitle("销售管理")
        
        # 订阅销售完成事件，自动刷新数据
        from core.event_bus import subscribe_event
        subscribe_event("sale_completed", self.on_sale_completed)
        
        layout = QVBoxLayout()
        
        self.tab_widget = QTabWidget()
        
        self.sale_list_tab = QWidget()
        self.sale_orders = []
        self.init_sale_list_tab()
        
        self.statistics_tab = QWidget()
        self.init_statistics_tab()
        
        self.tab_widget.addTab(self.sale_list_tab, "销售记录")
        self.tab_widget.addTab(self.statistics_tab, "销售统计")
        
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)
    
    def init_sale_list_tab(self):
        layout = QVBoxLayout()
        
        toolbar = QHBoxLayout()
        
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.start_date.setCalendarPopup(True)
        
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.load_sales)
        
        export_btn = QPushButton("导出Excel")
        export_btn.clicked.connect(self.export_sales)
        
        toolbar.addWidget(QLabel("开始日期:"))
        toolbar.addWidget(self.start_date)
        toolbar.addWidget(QLabel("结束日期:"))
        toolbar.addWidget(self.end_date)
        toolbar.addWidget(refresh_btn)
        toolbar.addWidget(export_btn)
        toolbar.addStretch()
        
        self.sale_table = QTableWidget()
        self.sale_table.setColumnCount(8)
        self.sale_table.setHorizontalHeaderLabels([
            "订单号", "会员", "总金额", "实付", "支付方式", 
            "收银员", "状态", "时间"])
        self.sale_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.sale_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.sale_table.setAlternatingRowColors(True)
        
        layout.addLayout(toolbar)
        layout.addWidget(self.sale_table)
        self.sale_list_tab.setLayout(layout)
    
    def init_statistics_tab(self):
        layout = QVBoxLayout()
        
        # 统计信息概览
        info_layout = QHBoxLayout()
        info_layout.setContentsMargins(10, 10, 10, 10)
        
        # 总销售额卡片
        self.total_amount_card = QWidget()
        self.total_amount_card.setStyleSheet("QWidget { background-color: #e6f7ff; border-radius: 8px; padding: 15px; }")
        amount_layout = QVBoxLayout()
        self.total_amount_label = QLabel("销售总额")
        self.total_amount_label.setStyleSheet("font-size: 14px; color: #1890ff;")
        self.total_amount_value = QLabel("¥0.00")
        self.total_amount_value.setStyleSheet("font-size: 24px; font-weight: bold; color: #1890ff;")
        amount_layout.addWidget(self.total_amount_label)
        amount_layout.addWidget(self.total_amount_value)
        self.total_amount_card.setLayout(amount_layout)
        
        # 订单数量卡片
        self.total_count_card = QWidget()
        self.total_count_card.setStyleSheet("QWidget { background-color: #f6ffed; border-radius: 8px; padding: 15px; }")
        count_layout = QVBoxLayout()
        self.total_count_label = QLabel("订单数量")
        self.total_count_label.setStyleSheet("font-size: 14px; color: #52c41a;")
        self.total_count_value = QLabel("0")
        self.total_count_value.setStyleSheet("font-size: 24px; font-weight: bold; color: #52c41a;")
        count_layout.addWidget(self.total_count_label)
        count_layout.addWidget(self.total_count_value)
        self.total_count_card.setLayout(count_layout)
        
        # 平均客单价卡片
        self.avg_amount_card = QWidget()
        self.avg_amount_card.setStyleSheet("QWidget { background-color: #fff7e6; border-radius: 8px; padding: 15px; }")
        avg_layout = QVBoxLayout()
        self.avg_amount_label = QLabel("平均客单价")
        self.avg_amount_label.setStyleSheet("font-size: 14px; color: #fa8c16;")
        self.avg_amount_value = QLabel("¥0.00")
        self.avg_amount_value.setStyleSheet("font-size: 24px; font-weight: bold; color: #fa8c16;")
        avg_layout.addWidget(self.avg_amount_label)
        avg_layout.addWidget(self.avg_amount_value)
        self.avg_amount_card.setLayout(avg_layout)
        
        # 毛利率卡片
        self.gross_profit_card = QWidget()
        self.gross_profit_card.setStyleSheet("QWidget { background-color: #f9f0ff; border-radius: 8px; padding: 15px; }")
        profit_layout = QVBoxLayout()
        self.gross_profit_label = QLabel("毛利率")
        self.gross_profit_label.setStyleSheet("font-size: 14px; color: #722ed1;")
        self.gross_profit_value = QLabel("0.00%")
        self.gross_profit_value.setStyleSheet("font-size: 24px; font-weight: bold; color: #722ed1;")
        profit_layout.addWidget(self.gross_profit_label)
        profit_layout.addWidget(self.gross_profit_value)
        self.gross_profit_card.setLayout(profit_layout)
        
        info_layout.addWidget(self.total_amount_card, 1)
        info_layout.addWidget(self.total_count_card, 1)
        info_layout.addWidget(self.avg_amount_card, 1)
        info_layout.addWidget(self.gross_profit_card, 1)
        
        # 时间范围选择
        time_range_layout = QHBoxLayout()
        time_range_layout.addWidget(QLabel("时间范围:"))
        self.time_range_combo = QComboBox()
        self.time_range_combo.addItem("7天", 7)
        self.time_range_combo.addItem("30天", 30)
        self.time_range_combo.addItem("90天", 90)
        self.time_range_combo.addItem("1年", 365)
        self.time_range_combo.currentIndexChanged.connect(self.load_statistics)
        
        refresh_stat_btn = QPushButton("刷新统计")
        refresh_stat_btn.clicked.connect(self.load_statistics)
        
        time_range_layout.addWidget(self.time_range_combo)
        time_range_layout.addStretch()
        time_range_layout.addWidget(refresh_stat_btn)
        
        # 销售趋势图表
        trend_layout = QVBoxLayout()
        trend_layout.addWidget(QLabel("销售趋势"))
        self.trend_chart = QChart()
        self.trend_chart.setAnimationOptions(QChart.SeriesAnimations)
        self.trend_chart.setTitle("每日销售额")
        self.trend_chart_view = QChartView(self.trend_chart)
        self.trend_chart_view.setRenderHint(QPainter.Antialiasing)
        self.trend_chart_view.setMinimumHeight(300)
        trend_layout.addWidget(self.trend_chart_view)
        
        # 热销商品图表
        top_products_layout = QVBoxLayout()
        top_products_layout.addWidget(QLabel("热销商品"))
        self.top_products_chart = QChart()
        self.top_products_chart.setAnimationOptions(QChart.SeriesAnimations)
        self.top_products_chart.setTitle("销售额前10商品")
        self.top_products_chart_view = QChartView(self.top_products_chart)
        self.top_products_chart_view.setRenderHint(QPainter.Antialiasing)
        self.top_products_chart_view.setMinimumHeight(300)
        top_products_layout.addWidget(self.top_products_chart_view)
        
        # 促销建议
        suggestion_layout = QVBoxLayout()
        suggestion_layout.addWidget(QLabel("促销建议"))
        self.suggestion_list = QTableWidget()
        self.suggestion_list.setColumnCount(3)
        self.suggestion_list.setHorizontalHeaderLabels(["商品", "类型", "建议"])
        self.suggestion_list.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.suggestion_list.setAlternatingRowColors(True)
        self.suggestion_list.setMinimumHeight(200)
        suggestion_layout.addWidget(self.suggestion_list)
        
        # 组装所有布局
        layout.addLayout(info_layout)
        layout.addLayout(time_range_layout)
        layout.addLayout(trend_layout)
        layout.addLayout(top_products_layout)
        layout.addLayout(suggestion_layout)
        
        self.statistics_tab.setLayout(layout)
    
    def on_sale_completed(self, **kwargs):
        """当销售完成时触发，刷新销售数据"""
        logger.info("收到销售完成事件，正在刷新销售数据...")
        self.load_sales()
        self.load_statistics()
    
    def load_sales(self):
        try:
            with self.db_session() as db:
                controller = SaleController(db)
                start_date = self.start_date.date().toPyDate()
                end_date = self.end_date.date().toPyDate()
                
                self.sale_orders = controller.list_sale_orders(
                    start_date=start_date,
                    end_date=end_date
                )
                
                self.sale_table.setRowCount(len(self.sale_orders))
                
                for row, order in enumerate(self.sale_orders):
                    self.sale_table.setItem(row, 0, QTableWidgetItem(order.order_no))
                    
                    member_name = order.member.name if order.member else ""
                    self.sale_table.setItem(row, 1, QTableWidgetItem(member_name))
                    
                    self.sale_table.setItem(row, 2, QTableWidgetItem(f"¥{order.total_amount:.2f}"))
                    self.sale_table.setItem(row, 3, QTableWidgetItem(f"¥{order.actual_amount:.2f}"))
                    self.sale_table.setItem(row, 4, QTableWidgetItem(order.payment_method))
                    self.sale_table.setItem(row, 5, QTableWidgetItem(order.operator or ""))
                    self.sale_table.setItem(row, 6, QTableWidgetItem(order.status))
                    self.sale_table.setItem(row, 7, QTableWidgetItem(
                        order.create_time.strftime("%Y-%m-%d %H:%M")))
                    
                    for col in range(8):
                        self.sale_table.item(row, col).setFlags(
                            Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        
        except Exception as e:
            logger.error(f"加载销售记录失败: {e}")
    
    def load_statistics(self):
        try:
            # 获取时间范围
            days = self.time_range_combo.currentData()
            end_date = QDate.currentDate().toPyDate()
            start_date = (QDate.currentDate().addDays(-days)).toPyDate()
            
            with self.db_session() as db:
                controller = SaleController(db)
                
                # 加载基本统计数据
                stats = controller.get_sale_statistics(start_date, end_date)
                
                # 更新统计卡片
                self.total_amount_value.setText(f"¥{stats['total_amount']:.2f}")
                self.total_count_value.setText(f"{stats['total_count']}")
                self.avg_amount_value.setText(f"¥{stats['avg_amount']:.2f}")
                self.gross_profit_value.setText(f"{stats['gross_profit_rate']:.2f}%")
                
                # 加载并显示销售趋势图表
                self.load_sales_trend_chart(controller, start_date, end_date)
                
                # 加载并显示热销商品图表
                self.load_top_products_chart(controller, start_date, end_date)
                
                # 加载促销建议
                self.load_promotion_suggestions(controller)
        
        except Exception as e:
            logger.error(f"加载销售统计失败: {e}")
            QMessageBox.critical(self, "错误", f"加载销售统计失败: {str(e)}")
    
    def load_sales_trend_chart(self, controller, start_date, end_date):
        try:
            # 清除现有系列
            self.trend_chart.removeAllSeries()
            
            # 获取每日销售数据
            daily_sales = controller.get_daily_sales(start_date, end_date)
            
            if not daily_sales:
                self.trend_chart.setTitle("销售趋势 - 无数据")
                return
            
            # 创建折线系列
            series = QLineSeries()
            series.setName("销售额")
            series.setPen(QPen(QColor(52, 152, 219), 2))
            
            dates = []
            amounts = []
            
            for day in daily_sales:
                dates.append(day['date'])
                amounts.append(day['amount'])
                series.append(len(dates) - 1, day['amount'])
            
            # 添加系列到图表
            self.trend_chart.addSeries(series)
            
            # 创建轴
            axis_x = QBarCategoryAxis()
            axis_x.append(dates)
            axis_x.setTitleText("日期")
            
            axis_y = QValueAxis()
            axis_y.setTitleText("销售额 (¥)")
            
            self.trend_chart.setAxisX(axis_x, series)
            self.trend_chart.setAxisY(axis_y, series)
            
            self.trend_chart.setTitle(f"销售趋势 ({start_date} 至 {end_date})")
        
        except Exception as e:
            logger.error(f"加载销售趋势图表失败: {e}")
    
    def load_top_products_chart(self, controller, start_date, end_date):
        try:
            # 清除现有系列
            self.top_products_chart.removeAllSeries()
            
            # 获取商品销售数据
            product_sales = controller.get_product_sales(None, start_date, end_date)
            
            if not product_sales:
                self.top_products_chart.setTitle("热销商品 - 无数据")
                return
            
            # 按销售额排序，取前10
            product_sales.sort(key=lambda x: x['total_amount'], reverse=True)
            top_products = product_sales[:10]
            
            # 创建条形系列
            series = QBarSeries()
            
            # 创建一个商品条形集
            bar_set = QBarSet("销售额")
            for product in top_products:
                bar_set.append(product['total_amount'])
            
            series.append(bar_set)
            
            # 添加系列到图表
            self.top_products_chart.addSeries(series)
            
            # 创建轴
            axis_x = QBarCategoryAxis()
            axis_x.append([p['product_name'][:20] for p in top_products])
            axis_x.setTitleText("商品")
            axis_x.setLabelsAngle(-45)
            
            axis_y = QValueAxis()
            axis_y.setTitleText("销售额 (¥)")
            
            self.top_products_chart.setAxisX(axis_x, series)
            self.top_products_chart.setAxisY(axis_y, series)
            
            self.top_products_chart.setTitle(f"销售额前10商品 ({start_date} 至 {end_date})")
        
        except Exception as e:
            logger.error(f"加载热销商品图表失败: {e}")
    
    def load_promotion_suggestions(self, controller):
        try:
            # 获取促销建议
            suggestions = controller.get_promotion_suggestions()
            
            # 更新建议列表
            self.suggestion_list.setRowCount(len(suggestions))
            
            for row, suggestion in enumerate(suggestions):
                self.suggestion_list.setItem(row, 0, QTableWidgetItem(suggestion['product_name']))
                self.suggestion_list.setItem(row, 1, QTableWidgetItem(suggestion['type']))
                self.suggestion_list.setItem(row, 2, QTableWidgetItem(suggestion['suggestion']))
                
                # 设置行高
                self.suggestion_list.resizeRowToContents(row)
        
        except Exception as e:
            logger.error(f"加载促销建议失败: {e}")
    
    def export_sales(self):
        QMessageBox.information(self, "提示", "导出功能开发中...")
