from sqlalchemy.orm import Session
from shared.models.sale import SaleOrder, SaleItem
from shared.models.product import Product
from core.logger import logger
from datetime import datetime, timedelta

class SaleController:
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def get_sale_order(self, sale_id):
        return self.db.get(SaleOrder, sale_id)
    
    def get_sale_order_by_no(self, order_no):
        return self.db.query(SaleOrder).filter(SaleOrder.order_no == order_no).first()
    
    def list_sale_orders(self, start_date=None, end_date=None, operator=None, status=None):
        query = self.db.query(SaleOrder)
        
        if start_date:
            query = query.filter(SaleOrder.create_time >= start_date)
        if end_date:
            query = query.filter(SaleOrder.create_time <= end_date)
        if operator:
            query = query.filter(SaleOrder.operator == operator)
        if status:
            query = query.filter(SaleOrder.status == status)
        
        return query.order_by(SaleOrder.create_time.desc()).all()
    
    def get_sale_statistics(self, start_date=None, end_date=None):
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        orders = self.list_sale_orders(start_date, end_date, status='已完成')
        
        total_amount = sum(o.actual_amount for o in orders)
        total_count = len(orders)
        avg_amount = total_amount / total_count if total_count > 0 else 0
        
        total_gross_profit = 0.0
        for order in orders:
            order_profit = self.calculate_order_gross_profit(order.id)
            total_gross_profit += order_profit
        
        return {
            'total_amount': total_amount,
            'total_count': total_count,
            'avg_amount': avg_amount,
            'total_gross_profit': total_gross_profit,
            'gross_profit_rate': total_gross_profit / total_amount * 100 if total_amount > 0 else 0,
            'start_date': start_date,
            'end_date': end_date
        }
    
    def calculate_order_gross_profit(self, sale_id):
        sale_order = self.db.get(SaleOrder, sale_id)
        if not sale_order:
            return 0.0
        
        total_cost = 0.0
        for item in sale_order.items:
            product = self.db.get(Product, item.product_id)
            if product and product.price_cost:
                total_cost += item.quantity * product.price_cost
        
        return sale_order.actual_amount - total_cost
    
    def get_product_sales(self, product_id=None, start_date=None, end_date=None):
        query = self.db.query(SaleItem).join(SaleOrder)
        
        if product_id:
            query = query.filter(SaleItem.product_id == product_id)
        if start_date:
            query = query.filter(SaleOrder.create_time >= start_date)
        if end_date:
            query = query.filter(SaleOrder.create_time <= end_date)
        query = query.filter(SaleOrder.status == '已完成')
        
        items = query.all()
        
        product_stats = {}
        for item in items:
            product = self.db.get(Product, item.product_id)
            cost = product.price_cost if product and product.price_cost else 0.0
            gross_profit = item.amount - (item.quantity * cost)
            
            if item.product_id not in product_stats:
                product_stats[item.product_id] = {
                    'product_id': item.product_id,
                    'product_name': item.product.name if item.product else '',
                    'total_quantity': 0,
                    'total_amount': 0,
                    'total_cost': 0,
                    'total_gross_profit': 0
                }
            product_stats[item.product_id]['total_quantity'] += item.quantity
            product_stats[item.product_id]['total_amount'] += item.amount
            product_stats[item.product_id]['total_cost'] += item.quantity * cost
            product_stats[item.product_id]['total_gross_profit'] += gross_profit
        
        return list(product_stats.values())
    
    def get_daily_sales(self, start_date=None, end_date=None):
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        orders = self.list_sale_orders(start_date, end_date, status='已完成')
        
        daily_stats = {}
        for order in orders:
            date_key = order.create_time.strftime('%Y-%m-%d')
            if date_key not in daily_stats:
                daily_stats[date_key] = {
                    'date': date_key,
                    'amount': 0.0,
                    'count': 0,
                    'gross_profit': 0.0
                }
            daily_stats[date_key]['amount'] += order.actual_amount
            daily_stats[date_key]['count'] += 1
            daily_stats[date_key]['gross_profit'] += self.calculate_order_gross_profit(order.id)
        
        return sorted(daily_stats.values(), key=lambda x: x['date'])
    
    def get_promotion_suggestions(self, product_id=None):
        suggestions = []
        
        # 获取最近30天的销售数据
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        product_sales = self.get_product_sales(start_date=start_date, end_date=end_date)
        sales_map = {item['product_id']: item['total_quantity'] for item in product_sales}
        
        products = self.db.query(Product).all()
        for product in products:
            if product.stock_quantity <= product.min_stock:
                continue
            
            if product.stock_quantity >= product.max_stock:
                suggestions.append({
                    'type': '库存过高',
                    'product_id': product.id,
                    'product_name': product.name,
                    'suggestion': '建议促销清库存'
                })
            
            sale_count = sales_map.get(product.id, 0)
            if sale_count < 5:
                suggestions.append({
                    'type': '滞销商品',
                    'product_id': product.id,
                    'product_name': product.name,
                    'suggestion': '建议捆绑销售或打折促销'
                })
        
        return suggestions
