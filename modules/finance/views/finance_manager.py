from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView,
    QLabel, QTabWidget, QDateEdit, QComboBox
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis, QPieSeries, QPieSlice
from PyQt5.QtGui import QPainter, QColor
from sqlalchemy.orm import Session
from modules.finance.controllers import FinanceController
from core.logger import logger

class FinanceManager(QWidget):
    def __init__(self, db_session: Session, current_user):
        super().__init__()
        self.db_session = db_session
        self.current_user = current_user
        self.init_ui()
        # 延迟加载数据
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(0, self.load_all_data)
    
    def load_all_data(self):
        """加载所有财务数据"""
        self.load_statistics()
        self.load_receivables()
        self.load_payables()
    
    def init_ui(self):
        self.setWindowTitle("财务管理")
        
        # 订阅销售完成事件，自动刷新数据
        from core.event_bus import subscribe_event
        subscribe_event("sale_completed", self.on_sale_completed)
        
        layout = QVBoxLayout()
        
        # 顶部工具栏
        global_toolbar = QHBoxLayout()
        self.global_refresh_btn = QPushButton("刷新全部数据")
        self.global_refresh_btn.clicked.connect(self.load_all_data)
        global_toolbar.addStretch()
        global_toolbar.addWidget(self.global_refresh_btn)
        
        self.tab_widget = QTabWidget()
        
        self.statistics_tab = QWidget()
        self.init_statistics_tab()
        
        self.cash_flow_tab = QWidget()
        self.init_cash_flow_tab()
        
        self.receivables_tab = QWidget()
        self.init_receivables_tab()
        
        self.payables_tab = QWidget()
        self.init_payables_tab()
        
        self.tab_widget.addTab(self.statistics_tab, "营业统计")
        self.tab_widget.addTab(self.cash_flow_tab, "收支流水")
        self.tab_widget.addTab(self.receivables_tab, "应收账款")
        self.tab_widget.addTab(self.payables_tab, "应付账款")
        
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)
    
    def init_statistics_tab(self):
        layout = QVBoxLayout()
        
        toolbar = QHBoxLayout()
        
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.start_date.setCalendarPopup(True)
        
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.load_statistics)
        
        toolbar.addWidget(QLabel("开始日期:"))
        toolbar.addWidget(self.start_date)
        toolbar.addWidget(QLabel("结束日期:"))
        toolbar.addWidget(self.end_date)
        toolbar.addWidget(refresh_btn)
        toolbar.addStretch()
        
        # 财务概览卡片
        overview_layout = QHBoxLayout()
        overview_layout.setContentsMargins(10, 10, 10, 10)
        
        # 营业总额卡片
        self.total_amount_card = QWidget()
        self.total_amount_card.setStyleSheet("QWidget { background-color: #e6f7ff; border-radius: 8px; padding: 15px; }")
        amount_layout = QVBoxLayout()
        amount_label = QLabel("营业总额")
        amount_label.setStyleSheet("font-size: 14px; color: #1890ff;")
        self.total_amount_value = QLabel("¥0.00")
        self.total_amount_value.setStyleSheet("font-size: 24px; font-weight: bold; color: #1890ff;")
        amount_layout.addWidget(amount_label)
        amount_layout.addWidget(self.total_amount_value)
        self.total_amount_card.setLayout(amount_layout)
        
        # 订单数量卡片
        self.total_count_card = QWidget()
        self.total_count_card.setStyleSheet("QWidget { background-color: #f6ffed; border-radius: 8px; padding: 15px; }")
        count_layout = QVBoxLayout()
        count_label = QLabel("订单数量")
        count_label.setStyleSheet("font-size: 14px; color: #52c41a;")
        self.total_count_value = QLabel("0")
        self.total_count_value.setStyleSheet("font-size: 24px; font-weight: bold; color: #52c41a;")
        count_layout.addWidget(count_label)
        count_layout.addWidget(self.total_count_value)
        self.total_count_card.setLayout(count_layout)
        
        # 平均客单价卡片
        self.avg_amount_card = QWidget()
        self.avg_amount_card.setStyleSheet("QWidget { background-color: #fff7e6; border-radius: 8px; padding: 15px; }")
        avg_layout = QVBoxLayout()
        avg_label = QLabel("平均客单价")
        avg_label.setStyleSheet("font-size: 14px; color: #fa8c16;")
        self.avg_amount_value = QLabel("¥0.00")
        self.avg_amount_value.setStyleSheet("font-size: 24px; font-weight: bold; color: #fa8c16;")
        avg_layout.addWidget(avg_label)
        avg_layout.addWidget(self.avg_amount_value)
        self.avg_amount_card.setLayout(avg_layout)
        
        # 净利润卡片
        self.net_profit_card = QWidget()
        self.net_profit_card.setStyleSheet("QWidget { background-color: #f9f0ff; border-radius: 8px; padding: 15px; }")
        profit_layout = QVBoxLayout()
        profit_label = QLabel("净利润")
        profit_label.setStyleSheet("font-size: 14px; color: #722ed1;")
        self.net_profit_value = QLabel("¥0.00")
        self.net_profit_value.setStyleSheet("font-size: 24px; font-weight: bold; color: #722ed1;")
        profit_layout.addWidget(profit_label)
        profit_layout.addWidget(self.net_profit_value)
        self.net_profit_card.setLayout(profit_layout)
        
        overview_layout.addWidget(self.total_amount_card, 1)
        overview_layout.addWidget(self.total_count_card, 1)
        overview_layout.addWidget(self.avg_amount_card, 1)
        overview_layout.addWidget(self.net_profit_card, 1)
        
        # 图表区域
        chart_layout = QHBoxLayout()
        
        # 销售趋势图表
        self.trend_chart = QChart()
        self.trend_chart.setAnimationOptions(QChart.SeriesAnimations)
        self.trend_chart.setTitle("销售趋势")
        self.trend_chart_view = QChartView(self.trend_chart)
        self.trend_chart_view.setRenderHint(QPainter.Antialiasing)
        self.trend_chart_view.setMinimumHeight(300)
        self.trend_chart_view.setMinimumWidth(400)
        
        # 支付方式饼图
        self.payment_chart = QChart()
        self.payment_chart.setAnimationOptions(QChart.SeriesAnimations)
        self.payment_chart.setTitle("支付方式分布")
        self.payment_chart_view = QChartView(self.payment_chart)
        self.payment_chart_view.setRenderHint(QPainter.Antialiasing)
        self.payment_chart_view.setMinimumHeight(300)
        self.payment_chart_view.setMinimumWidth(400)
        
        chart_layout.addWidget(self.trend_chart_view, 1)
        chart_layout.addWidget(self.payment_chart_view, 1)
        
        # 支付方式明细
        self.payment_table = QTableWidget()
        self.payment_table.setColumnCount(4)
        self.payment_table.setHorizontalHeaderLabels(["支付方式", "金额", "笔数", "占比"])
        self.payment_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.payment_table.setAlternatingRowColors(True)
        
        layout.addLayout(toolbar)
        layout.addLayout(overview_layout)
        layout.addLayout(chart_layout)
        layout.addWidget(QLabel("支付方式明细:"))
        layout.addWidget(self.payment_table)
        self.statistics_tab.setLayout(layout)
    
    def init_cash_flow_tab(self):
        layout = QVBoxLayout()
        
        label = QLabel("流水记录功能开发中...")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 16px; color: #95a5a6;")
        
        layout.addWidget(label)
        self.cash_flow_tab.setLayout(layout)
    
    def load_statistics(self):
        try:
            start_date = self.start_date.date().toPyDate()
            end_date = self.end_date.date().toPyDate()
            
            with self.db_session() as db:
                controller = FinanceController(db)
                
                # 获取收入统计
                stats = controller.get_revenue_statistics(start_date, end_date)
                
                # 确保返回的字典包含所有必要的键
                if not isinstance(stats, dict):
                    logger.error("加载财务统计失败: 控制器返回的数据不是字典")
                    return
                
                # 检查必要的键是否存在
                required_keys = ['total_amount', 'order_count', 'avg_amount', 'by_payment_method']
                for key in required_keys:
                    if key not in stats:
                        logger.error(f"加载财务统计失败: 缺少必要的键 '{key}'")
                        return
                
                # 获取财务摘要
                finance_summary = controller.get_finance_summary(start_date, end_date)
                
                # 更新统计卡片
                self.total_amount_value.setText(f"¥{stats['total_amount']:.2f}")
                self.total_count_value.setText(str(stats['order_count']))
                self.avg_amount_value.setText(f"¥{stats['avg_amount']:.2f}")
                self.net_profit_value.setText(f"¥{finance_summary['net_profit']:.2f}")
                
                # 更新销售趋势图表
                self.update_trend_chart(controller, start_date, end_date)
                
                # 更新支付方式图表和表格
                by_method = stats['by_payment_method']
                if isinstance(by_method, dict):
                    self.update_payment_chart(by_method)
                    
                    self.payment_table.setRowCount(len(by_method))
                    
                    for row, (method, data) in enumerate(by_method.items()):
                        if isinstance(data, dict) and 'amount' in data and 'count' in data:
                            self.payment_table.setItem(row, 0, QTableWidgetItem(method))
                            self.payment_table.setItem(row, 1, QTableWidgetItem(f"¥{data['amount']:.2f}"))
                            self.payment_table.setItem(row, 2, QTableWidgetItem(str(data['count'])))
                            
                            percentage = (data['amount'] / stats['total_amount'] * 100) if stats['total_amount'] > 0 else 0
                            self.payment_table.setItem(row, 3, QTableWidgetItem(f"{percentage:.1f}%"))
                            
                            for col in range(4):
                                self.payment_table.item(row, col).setFlags(
                                    Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        
        except Exception as e:
            logger.error(f"加载财务统计失败: {e}")
            import traceback
            traceback.print_exc()
    
    def update_trend_chart(self, controller, start_date, end_date):
        """更新销售趋势图表"""
        self.trend_chart.removeAllSeries()
        
        # 移除旧的坐标轴
        for axis in self.trend_chart.axes():
            self.trend_chart.removeAxis(axis)
        
        try:
            daily_data = controller.get_daily_finance(start_date, end_date)
            
            if not daily_data:
                self.trend_chart.setTitle("销售趋势 - 无数据")
                return
            
            # 创建销售额系列
            sales_series = QLineSeries()
            sales_series.setName("销售额")
            sales_series.setPen(QColor(52, 152, 219, 255))
            
            # 创建利润系列
            profit_series = QLineSeries()
            profit_series.setName("利润")
            profit_series.setPen(QColor(46, 204, 113, 255))
            
            dates = []
            for i, data in enumerate(daily_data):
                dates.append(data['date'])
                sales_series.append(i, data['sales'])
                profit_series.append(i, data['profit'])
            
            # 添加系列到图表
            self.trend_chart.addSeries(sales_series)
            self.trend_chart.addSeries(profit_series)
            
            # 创建轴
            axis_x = QBarCategoryAxis()
            axis_x.append(dates)
            axis_x.setLabelsAngle(-45)
            
            axis_y = QValueAxis()
            axis_y.setTitleText("金额 (¥)")
            
            # 计算合适的Y轴范围
            all_values = []
            for data in daily_data:
                all_values.append(data['sales'])
                all_values.append(data['profit'])
            
            if all_values:
                max_val = max(all_values)
                min_val = min(all_values)
                # 稍微扩大一点范围
                range_val = max_val - min_val
                if range_val == 0:
                    range_val = 100
                
                # 确保最小值不超过0太多（除非有亏损）
                y_min = min(0, min_val - range_val * 0.1)
                y_max = max_val + range_val * 0.1
                
                axis_y.setRange(y_min, y_max)
            
            self.trend_chart.setAxisX(axis_x, sales_series)
            self.trend_chart.setAxisY(axis_y, sales_series)
            self.trend_chart.setAxisX(axis_x, profit_series)
            self.trend_chart.setAxisY(axis_y, profit_series)
            
            self.trend_chart.setTitle(f"销售趋势 ({start_date} 至 {end_date})")
        
        except Exception as e:
            logger.error(f"更新销售趋势图表失败: {e}")
    
    def update_payment_chart(self, payment_stats):
        """更新支付方式分布饼图"""
        # from PyQt5.QtChart import QPieSeries, QPieSlice # Already imported
        
        self.payment_chart.removeAllSeries()
        
        series = QPieSeries()
        
        colors = [
            QColor(52, 152, 219),  # 蓝色
            QColor(46, 204, 113),  # 绿色
            QColor(241, 196, 15),  # 黄色
            QColor(231, 76, 60),  # 红色
            QColor(155, 89, 182),  # 紫色
            QColor(52, 73, 94),  # 深蓝灰色
            QColor(230, 126, 34),  # 橙色
            QColor(41, 128, 185)   # 靛蓝色
        ]
        
        color_index = 0
        for method, data in payment_stats.items():
            if isinstance(data, dict) and 'amount' in data:
                # QPieSeries.append(label, value)
                slice = series.append(f"{method} (¥{data['amount']:.2f})", data['amount'])
                slice.setBrush(colors[color_index % len(colors)])
                color_index += 1
        
        self.payment_chart.addSeries(series)
    
    def init_cash_flow_tab(self):
        layout = QVBoxLayout()
        
        toolbar = QHBoxLayout()
        
        self.flow_start_date = QDateEdit()
        self.flow_start_date.setDate(QDate.currentDate().addDays(-30))
        self.flow_start_date.setCalendarPopup(True)
        
        self.flow_end_date = QDateEdit()
        self.flow_end_date.setDate(QDate.currentDate())
        self.flow_end_date.setCalendarPopup(True)
        
        self.flow_type_combo = QComboBox()
        self.flow_type_combo.addItem("全部", None)
        self.flow_type_combo.addItem("收入", "收入")
        self.flow_type_combo.addItem("支出", "支出")
        
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.load_cash_flow)
        
        toolbar.addWidget(QLabel("开始日期:"))
        toolbar.addWidget(self.flow_start_date)
        toolbar.addWidget(QLabel("结束日期:"))
        toolbar.addWidget(self.flow_end_date)
        toolbar.addWidget(QLabel("类型:"))
        toolbar.addWidget(self.flow_type_combo)
        toolbar.addWidget(refresh_btn)
        toolbar.addStretch()
        
        self.flow_table = QTableWidget()
        self.flow_table.setColumnCount(6)
        self.flow_table.setHorizontalHeaderLabels(["日期", "类型", "金额", "来源/去向", "备注", "操作员"])
        self.flow_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.flow_table.setAlternatingRowColors(True)
        
        layout.addLayout(toolbar)
        layout.addWidget(self.flow_table)
        self.cash_flow_tab.setLayout(layout)
    
    def on_sale_completed(self, **kwargs):
        """当销售完成时触发，刷新财务数据"""
        logger.info("收到销售完成事件，正在刷新财务数据...")
        self.load_all_data()

    def load_cash_flow(self):
        # 实现收支流水加载功能
        # 这里可以从销售订单和采购订单中获取收支记录
        pass
    
    def init_receivables_tab(self):
        layout = QVBoxLayout()
        
        toolbar = QHBoxLayout()
        
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.load_receivables)
        
        toolbar.addWidget(refresh_btn)
        toolbar.addStretch()
        
        self.receivables_table = QTableWidget()
        self.receivables_table.setColumnCount(5)
        self.receivables_table.setHorizontalHeaderLabels(["订单号", "供应商", "金额", "创建时间", "状态"])
        self.receivables_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.receivables_table.setAlternatingRowColors(True)
        
        layout.addLayout(toolbar)
        layout.addWidget(self.receivables_table)
        self.receivables_tab.setLayout(layout)
    
    def load_receivables(self):
        try:
            with self.db_session() as db:
                controller = FinanceController(db)
                receivables = controller.get_receivables()
                
                self.receivables_table.setRowCount(len(receivables))
                
                for row, item in enumerate(receivables):
                    self.receivables_table.setItem(row, 0, QTableWidgetItem(item['order_no']))
                    self.receivables_table.setItem(row, 1, QTableWidgetItem(item['supplier']))
                    self.receivables_table.setItem(row, 2, QTableWidgetItem(f"¥{item['amount']:.2f}"))
                    self.receivables_table.setItem(row, 3, QTableWidgetItem(item['create_time'].strftime("%Y-%m-%d %H:%M")))
                    self.receivables_table.setItem(row, 4, QTableWidgetItem("待付款"))
                    
                    for col in range(5):
                        self.receivables_table.item(row, col).setFlags(
                            Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        
        except Exception as e:
            logger.error(f"加载应收账款失败: {e}")
    
    def init_payables_tab(self):
        layout = QVBoxLayout()
        
        toolbar = QHBoxLayout()
        
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.load_payables)
        
        toolbar.addWidget(refresh_btn)
        toolbar.addStretch()
        
        self.payables_table = QTableWidget()
        self.payables_table.setColumnCount(5)
        self.payables_table.setHorizontalHeaderLabels(["订单号", "会员", "金额", "创建时间", "状态"])
        self.payables_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.payables_table.setAlternatingRowColors(True)
        
        layout.addLayout(toolbar)
        layout.addWidget(self.payables_table)
        self.payables_tab.setLayout(layout)
    
    def load_payables(self):
        try:
            with self.db_session() as db:
                controller = FinanceController(db)
                payables = controller.get_payables()
                
                self.payables_table.setRowCount(len(payables))
                
                for row, item in enumerate(payables):
                    self.payables_table.setItem(row, 0, QTableWidgetItem(item['order_no']))
                    self.payables_table.setItem(row, 1, QTableWidgetItem(item['member']))
                    self.payables_table.setItem(row, 2, QTableWidgetItem(f"¥{item['amount']:.2f}"))
                    self.payables_table.setItem(row, 3, QTableWidgetItem(item['create_time'].strftime("%Y-%m-%d %H:%M")))
                    self.payables_table.setItem(row, 4, QTableWidgetItem("待退款"))
                    
                    for col in range(5):
                        self.payables_table.item(row, col).setFlags(
                            Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        
        except Exception as e:
            logger.error(f"加载应付账款失败: {e}")
