from sqlalchemy.orm import Session
from shared.models.sale import SaleOrder, SaleItem
from shared.models.product import Product
from shared.models.member import Member
from shared.models.stock_log import StockLog
from shared.utils.order_generator import generate_sale_order_no
from core.logger import logger
from core.event_bus import publish_event

class SaleController:
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def create_sale_order(self, items, payment_method, member_id=None, operator=""):
        try:
            total_amount = 0.0
            discount_amount = 0.0
            member_points = 0
            discount_rate = 1.0
            
            member = None
            if member_id:
                member = self.db.get(Member, member_id)
                if member and member.grade == '黄金会员':
                    discount_rate = 0.95
                elif member and member.grade == '白金会员':
                    discount_rate = 0.90
            
            for item in items:
                item_total = item['quantity'] * item['price']
                total_amount += item_total
            
            if member and discount_rate < 1.0:
                discount_amount = total_amount * (1 - discount_rate)
                total_amount *= discount_rate
                member_points = int(total_amount / 10)
            
            sale_order = SaleOrder(
                order_no=generate_sale_order_no(),
                member_id=member_id,
                total_amount=total_amount,
                discount_amount=discount_amount,
                actual_amount=total_amount,
                payment_method=payment_method,
                status='已完成',
                operator=operator
            )
            self.db.add(sale_order)
            self.db.flush()
            
            for item in items:
                product = self.db.get(Product, item['product_id'])
                if not product:
                    logger.warning(f"商品不存在: {item['product_id']}")
                    continue

                cost_price = product.price_cost if product else 0.0

                sale_item = SaleItem(
                    sale_id=sale_order.id,
                    product_id=item['product_id'],
                    quantity=item['quantity'],
                    price=item['price'],
                    cost_price=cost_price,
                    amount=item['quantity'] * item['price'],
                    discount=0.0
                )
                self.db.add(sale_item)
                
                if product:
                    product.stock_quantity -= item['quantity']
                    
                    stock_log = StockLog(
                        product_id=item['product_id'],
                        type='出库',
                        quantity=-item['quantity'],
                        related_order_no=sale_order.order_no,
                        operator=operator,
                        remark='销售出库'
                    )
                    self.db.add(stock_log)
            
            if member and member_points > 0:
                member.points += member_points
            
            self.db.commit()
            logger.info(f"创建销售订单: {sale_order.order_no}")
            publish_event('sale_created', sale_id=sale_order.id)
            publish_event('sale_completed', sale_id=sale_order.id)
            
            return sale_order
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建销售订单失败: {e}")
            raise
    
    def return_sale_order(self, sale_id, return_items, operator=""):
        try:
            sale_order = self.db.get(SaleOrder, sale_id)
            if not sale_order or sale_order.status != '已完成':
                raise ValueError("销售订单状态不正确")
            
            for return_item in return_items:
                sale_item = next((item for item in sale_order.items if item.id == return_item['sale_item_id']), None)
                if not sale_item:
                    continue
                
                return_quantity = min(return_item['quantity'], sale_item.quantity)
                
                product = self.db.get(Product, sale_item.product_id)
                if product:
                    product.stock_quantity += return_quantity
                    
                    stock_log = StockLog(
                        product_id=sale_item.product_id,
                        type='入库',
                        quantity=return_quantity,
                        related_order_no=f"{sale_order.order_no}-退",
                        operator=operator,
                        remark='销售退货'
                    )
                    self.db.add(stock_log)
                
                refund_amount = return_quantity * sale_item.price
                sale_order.actual_amount -= refund_amount
            
            sale_order.status = '已退货'
            self.db.commit()
            logger.info(f"销售退货: {sale_order.order_no}")
            publish_event('sale_returned', sale_id=sale_id)
            
            return sale_order
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"销售退货失败: {e}")
            raise
    
    def generate_receipt(self, sale_id):
        sale_order = self.db.get(SaleOrder, sale_id)
        if not sale_order:
            return None
        
        receipt = {
            'order_no': sale_order.order_no,
            'create_time': sale_order.create_time,
            'operator': sale_order.operator,
            'payment_method': sale_order.payment_method,
            'total_amount': sale_order.total_amount,
            'discount_amount': sale_order.discount_amount,
            'actual_amount': sale_order.actual_amount,
            'items': []
        }
        
        for item in sale_order.items:
            receipt['items'].append({
                'name': item.product.name if item.product else '',
                'quantity': item.quantity,
                'price': item.price,
                'amount': item.amount
            })
        
        return receipt
    
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
