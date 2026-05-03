from sqlalchemy.orm import Session
from sqlalchemy import func
from shared.models.sale import SaleOrder
from shared.models.purchase import PurchaseOrder
from core.logger import logger
from datetime import datetime, timedelta

class FinanceController:
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def _get_db(self):
        # 兼容旧代码，但建议直接使用self.db
        return self.db
    
    def get_finance_summary(self, start_date=None, end_date=None):
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        try:
            # 直接使用self.db
            sales = self.db.query(SaleOrder).filter(
                SaleOrder.create_time >= start_date,
                SaleOrder.create_time <= end_date,
                SaleOrder.status == '已完成'
            ).all()
            
            total_sales = sum(s.actual_amount for s in sales)
            total_sale_count = len(sales)
            
            # Calculate profit based on Cost of Goods Sold (COGS)
            total_cost = 0.0
            for sale in sales:
                for item in sale.items:
                    # Use stored cost_price if available, otherwise fallback to product current cost
                    cost = item.cost_price if hasattr(item, 'cost_price') and item.cost_price is not None else (item.product.price_cost if item.product else 0.0)
                    total_cost += cost * item.quantity

            purchases = self.db.query(PurchaseOrder).filter(
                PurchaseOrder.create_time >= start_date,
                PurchaseOrder.create_time <= end_date,
                PurchaseOrder.status == '已完成'
            ).all()
            
            total_purchases = sum(p.total_amount for p in purchases)
            total_purchase_count = len(purchases)
            
            net_profit = total_sales - total_cost
            
            return {
                'total_sales': total_sales,
                'total_sale_count': total_sale_count,
                'total_purchases': total_purchases,
                'total_purchase_count': total_purchase_count,
                'net_profit': net_profit,
                'start_date': start_date,
                'end_date': end_date
            }
        except Exception as e:
            # 记录错误并返回默认值
            logger.error(f"获取财务摘要失败: {e}")
            return {
                'total_sales': 0.0,
                'total_sale_count': 0,
                'total_purchases': 0.0,
                'total_purchase_count': 0,
                'net_profit': 0.0,
                'start_date': start_date,
                'end_date': end_date
            }
    
    def get_daily_finance(self, start_date=None, end_date=None):
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        daily_data = {}
        
        try:
            # 直接使用self.db
            sales = self.db.query(SaleOrder).filter(
                SaleOrder.create_time >= start_date,
                SaleOrder.create_time <= end_date,
                SaleOrder.status == '已完成'
            ).all()
            
            for sale in sales:
                date_key = sale.create_time.strftime('%Y-%m-%d')
                if date_key not in daily_data:
                    daily_data[date_key] = {
                        'date': date_key,
                        'sales': 0.0,
                        'purchases': 0.0,
                        'profit': 0.0,
                        'cost': 0.0
                    }
                daily_data[date_key]['sales'] += sale.actual_amount
                
                # Calculate cost for this sale
                sale_cost = 0.0
                for item in sale.items:
                    item_cost = item.cost_price if hasattr(item, 'cost_price') and item.cost_price is not None else (item.product.price_cost if item.product else 0.0)
                    sale_cost += item_cost * item.quantity
                
                daily_data[date_key]['cost'] += sale_cost
            
            purchases = self.db.query(PurchaseOrder).filter(
                PurchaseOrder.create_time >= start_date,
                PurchaseOrder.create_time <= end_date,
                PurchaseOrder.status == '已完成'
            ).all()
            
            for purchase in purchases:
                date_key = purchase.create_time.strftime('%Y-%m-%d')
                if date_key not in daily_data:
                    daily_data[date_key] = {
                        'date': date_key,
                        'sales': 0.0,
                        'purchases': 0.0,
                        'profit': 0.0,
                        'cost': 0.0
                    }
                daily_data[date_key]['purchases'] += purchase.total_amount
        except Exception as e:
            # 记录错误并返回空数据
            logger.error(f"获取每日财务数据失败: {e}")
            daily_data = {}
        
        for data in daily_data.values():
            data['profit'] = data['sales'] - data['cost']
        
        return sorted(daily_data.values(), key=lambda x: x['date'])
    
    def get_payment_method_stats(self, start_date=None, end_date=None):
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        payment_stats = {}
        
        try:
            # 直接使用self.db
            sales = self.db.query(SaleOrder).filter(
                SaleOrder.create_time >= start_date,
                SaleOrder.create_time <= end_date,
                SaleOrder.status == '已完成'
            ).all()
            
            for sale in sales:
                method = sale.payment_method or '其他'
                if method not in payment_stats:
                    payment_stats[method] = {'amount': 0.0, 'count': 0}
                payment_stats[method]['amount'] += sale.actual_amount
                payment_stats[method]['count'] += 1
        except Exception as e:
            # 记录错误并返回空列表
            logger.error(f"获取支付方式统计失败: {e}")
            payment_stats = {}
        
        return [
            {'method': method, 'amount': data['amount'], 'count': data['count']}
            for method, data in payment_stats.items()
        ]
    
    def get_receivables(self):
        try:
            # 直接使用self.db
            orders = self.db.query(PurchaseOrder).filter(
                PurchaseOrder.status == '待入库'
            ).all()
            
            return [
                {
                    'order_no': o.order_no,
                    'supplier': o.supplier.name if o.supplier else '',
                    'amount': o.total_amount,
                    'create_time': o.create_time
                }
                for o in orders
            ]
        except Exception as e:
            # 记录错误并返回空列表
            logger.error(f"获取应收账款失败: {e}")
            return []
    
    def get_payables(self):
        try:
            # 直接使用self.db
            orders = self.db.query(SaleOrder).filter(
                SaleOrder.status == '已退货'
            ).all()
            
            return [
                {
                    'order_no': o.order_no,
                    'member': o.member.name if o.member else '',
                    'amount': o.actual_amount,
                    'create_time': o.create_time
                }
                for o in orders
            ]
        except Exception as e:
            # 记录错误并返回空列表
            logger.error(f"获取应付账款失败: {e}")
            return []
    
    def get_revenue_statistics(self, start_date=None, end_date=None):
        # 实现收入统计方法，返回FinanceManager期望的结构
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        total_amount = 0.0
        order_count = 0
        avg_amount = 0.0
        payment_stats = {}
        
        try:
            # 直接使用self.db
            sales = self.db.query(SaleOrder).filter(
                SaleOrder.create_time >= start_date,
                SaleOrder.create_time <= end_date,
                SaleOrder.status == '已完成'
            ).all()
            
            total_amount = sum(s.actual_amount for s in sales)
            order_count = len(sales)
            avg_amount = total_amount / order_count if order_count > 0 else 0
            
            # 获取支付方式统计
            for sale in sales:
                method = sale.payment_method or '其他'
                if method not in payment_stats:
                    payment_stats[method] = {'amount': 0.0, 'count': 0}
                payment_stats[method]['amount'] += sale.actual_amount
                payment_stats[method]['count'] += 1
        except Exception as e:
            # 记录错误并返回默认值
            logger.error(f"获取收入统计失败: {e}")
            # 即使出错也返回一个有效的字典，避免FinanceManager崩溃
            payment_stats = {}
        
        by_payment_method = payment_stats
        
        return {
            'total_amount': total_amount,
            'order_count': order_count,
            'avg_amount': avg_amount,
            'by_payment_method': by_payment_method,
            'start_date': start_date,
            'end_date': end_date
        }
