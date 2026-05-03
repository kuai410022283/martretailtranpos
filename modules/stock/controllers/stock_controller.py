from sqlalchemy.orm import Session
from shared.models.product import Product
from shared.models.stock_log import StockLog
from core.logger import logger
from core.event_bus import publish_event

class StockController:
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def get_stock_info(self, product_id):
        product = self.db.get(Product, product_id)
        if not product:
            return None
        
        return {
            'product': product,
            'stock_quantity': product.stock_quantity,
            'min_stock': product.min_stock,
            'max_stock': product.max_stock,
            'is_low': product.stock_quantity <= product.min_stock
        }
    
    def list_stock(self, category_id=None, low_stock_only=False, keyword=None):
        query = self.db.query(Product)
        
        if category_id:
            query = query.filter(Product.category_id == category_id)
        if low_stock_only:
            query = query.filter(Product.stock_quantity <= Product.min_stock)
        if keyword:
            query = query.filter(
                (Product.name.contains(keyword)) | 
                (Product.code.contains(keyword)) |
                (Product.barcode.contains(keyword))
            )
        
        return query.order_by(Product.stock_quantity.asc()).all()
    
    def get_low_stock_products(self):
        return self.db.query(Product).filter(
            Product.stock_quantity <= Product.min_stock,
            Product.status == '正常'
        ).order_by(Product.stock_quantity.asc()).all()
    
    def get_stock_logs(self, product_id=None, start_date=None, end_date=None, log_type=None):
        query = self.db.query(StockLog)
        
        if product_id:
            query = query.filter(StockLog.product_id == product_id)
        if start_date:
            query = query.filter(StockLog.create_time >= start_date)
        if end_date:
            query = query.filter(StockLog.create_time <= end_date)
        if log_type:
            query = query.filter(StockLog.type == log_type)
        
        # 执行查询并返回结果
        logs = query.order_by(StockLog.create_time.desc()).all()
        # 确保所有操作都在会话内完成
        return logs
    
    def adjust_stock(self, product_id, quantity, type="调整", operator="", remark="", cost_price=None):
        try:
            product = self.db.get(Product, product_id)
            if not product:
                raise ValueError("商品不存在")
            
            product.stock_quantity += quantity
            
            # 使用传入的成本价，或者产品的成本价，或者0
            actual_cost = cost_price if cost_price is not None else (product.price_cost or 0.0)

            stock_log = StockLog(
                product_id=product_id,
                type=type,
                quantity=quantity,
                cost_price=actual_cost,
                operator=operator,
                remark=remark
            )
            self.db.add(stock_log)
            
            self.db.commit()
            logger.info(f"库存调整: {product.name} {type} {quantity}")
            publish_event('stock_adjusted', product_id=product_id)
            return True
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"库存调整失败: {e}")
            raise
    
    def create_check_record(self, products, operator=""):
        try:
            for item in products:
                product_id = item['product_id']
                actual_quantity = item['actual_quantity']
                
                product = self.db.get(Product, product_id)
                if not product:
                    continue
                
                diff = actual_quantity - product.stock_quantity
                if diff != 0:
                    product.stock_quantity = actual_quantity
                    
                    log_type = '盘盈' if diff > 0 else '盘亏'
                    stock_log = StockLog(
                        product_id=product_id,
                        type=log_type,
                        quantity=diff,
                        cost_price=product.price_cost or 0.0,
                        operator=operator,
                        remark='库存盘点'
                    )
                    self.db.add(stock_log)
            
            self.db.commit()
            logger.info(f"库存盘点完成")
            publish_event('stock_check_completed')
            return True
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"库存盘点失败: {e}")
            raise
    
    def list_stock_logs(self, product_id=None, start_date=None, end_date=None, log_type=None):
        # 实现list_stock_logs方法，调用现有的get_stock_logs方法
        return self.get_stock_logs(product_id, start_date, end_date, log_type)
