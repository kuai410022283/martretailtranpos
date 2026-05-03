from sqlalchemy.orm import Session
from shared.models.purchase import PurchaseOrder, PurchaseItem
from shared.models.supplier import Supplier
from shared.models.product import Product
from shared.models.stock_log import StockLog
from shared.utils.order_generator import generate_purchase_order_no
from core.logger import logger
from core.event_bus import publish_event

class PurchaseController:
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def create_supplier(self, **kwargs):
        if 'code' not in kwargs or not kwargs['code']:
            kwargs['code'] = generate_purchase_order_no().replace('PO', 'S')
        
        supplier = Supplier(**kwargs)
        self.db.add(supplier)
        self.db.commit()
        logger.info(f"创建供应商: {supplier.code} - {supplier.name}")
        return supplier
    
    def get_supplier(self, supplier_id):
        return self.db.get(Supplier, supplier_id)
    
    def get_supplier_by_code(self, code):
        return self.db.query(Supplier).filter(Supplier.code == code).first()
    
    def list_suppliers(self, keyword=None):
        query = self.db.query(Supplier)
        if keyword:
            query = query.filter(
                (Supplier.name.contains(keyword)) | 
                (Supplier.code.contains(keyword))
            )
        return query.order_by(Supplier.create_time.desc()).all()
    
    def update_supplier(self, supplier_id, **kwargs):
        supplier = self.get_supplier(supplier_id)
        if not supplier:
            return None
        
        for key, value in kwargs.items():
            if hasattr(supplier, key):
                setattr(supplier, key, value)
        
        self.db.commit()
        logger.info(f"更新供应商: {supplier.code} - {supplier.name}")
        return supplier
    
    def delete_supplier(self, supplier_id):
        supplier = self.get_supplier(supplier_id)
        if not supplier:
            return False
        
        self.db.delete(supplier)
        self.db.commit()
        logger.info(f"删除供应商: {supplier.code} - {supplier.name}")
        return True
    
    def create_purchase_order(self, supplier_id, items, operator="", order_type="采购", ref_order_no=None, remark=""):
        try:
            total_amount = 0.0
            for item in items:
                total_amount += item['quantity'] * item['price']
            
            order_no = generate_purchase_order_no()
            if order_type == '退货':
                order_no = order_no.replace('PO', 'PR')
                status = '待退货'
            else:
                status = '待入库'

            purchase_order = PurchaseOrder(
                order_no=order_no,
                supplier_id=supplier_id,
                total_amount=total_amount,
                status=status,
                remark=remark,
                order_type=order_type,
                ref_order_no=ref_order_no
            )
            self.db.add(purchase_order)
            self.db.flush()
            
            for item in items:
                purchase_item = PurchaseItem(
                    purchase_id=purchase_order.id,
                    product_id=item['product_id'],
                    quantity=item['quantity'],
                    price=item['price'],
                    amount=item['quantity'] * item['price']
                )
                self.db.add(purchase_item)
            
            self.db.commit()
            logger.info(f"创建采购订单: {purchase_order.order_no}")
            publish_event('purchase_created', purchase_id=purchase_order.id)
            return purchase_order
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建采购订单失败: {e}")
            raise
    
    def get_purchase_order(self, purchase_id):
        return self.db.get(PurchaseOrder, purchase_id)
    
    def get_purchase_order_by_no(self, order_no):
        return self.db.query(PurchaseOrder).filter(PurchaseOrder.order_no == order_no).first()
    
    def list_purchase_orders(self, status=None, supplier_id=None, keyword=None, order_type=None):
        query = self.db.query(PurchaseOrder)
        if status:
            query = query.filter(PurchaseOrder.status == status)
        if supplier_id:
            query = query.filter(PurchaseOrder.supplier_id == supplier_id)
        if keyword:
            query = query.filter(PurchaseOrder.order_no.contains(keyword))
        if order_type:
            query = query.filter(PurchaseOrder.order_type == order_type)
        return query.order_by(PurchaseOrder.create_time.desc()).all()
    
    def update_purchase_order(self, purchase_id, **kwargs):
        purchase_order = self.get_purchase_order(purchase_id)
        if not purchase_order:
            return None
        
        for key, value in kwargs.items():
            if hasattr(purchase_order, key):
                setattr(purchase_order, key, value)
        
        self.db.commit()
        logger.info(f"更新采购订单: {purchase_order.order_no}")
        return purchase_order

    def update_purchase_order_with_items(self, purchase_id, supplier_id, items, remark, operator=""):
        try:
            purchase_order = self.get_purchase_order(purchase_id)
            if not purchase_order:
                raise ValueError("订单不存在")
            
            if purchase_order.status not in ['待入库', '待退货']:
                 raise ValueError("只能修改待处理的订单")

            purchase_order.supplier_id = supplier_id
            purchase_order.remark = remark
            
            # 清空旧项目
            # 由于定义了 cascade="all, delete-orphan"，这将删除数据库中的记录
            purchase_order.items = []
            self.db.flush()
            
            total_amount = 0.0
            for item in items:
                amount = item['quantity'] * item['price']
                total_amount += amount
                purchase_item = PurchaseItem(
                    purchase_id=purchase_order.id,
                    product_id=item['product_id'],
                    quantity=item['quantity'],
                    price=item['price'],
                    amount=amount
                )
                self.db.add(purchase_item)
            
            purchase_order.total_amount = total_amount
            
            self.db.commit()
            logger.info(f"更新采购订单及明细: {purchase_order.order_no}")
            return purchase_order
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新采购订单失败: {e}")
            raise
    
    def receive_purchase_order(self, purchase_id, operator=""):
        try:
            purchase_order = self.get_purchase_order(purchase_id)
            if not purchase_order:
                raise ValueError("订单不存在")

            import datetime
            now = datetime.datetime.now()

            if purchase_order.order_type == '采购':
                if purchase_order.status != '待入库':
                    raise ValueError("采购订单状态不正确")
                
                for item in purchase_order.items:
                    product = self.db.get(Product, item.product_id)
                    if product:
                        # 计算加权平均成本
                        current_value = product.stock_quantity * (product.price_cost or 0.0)
                        purchase_value = item.quantity * item.price
                        total_qty = product.stock_quantity + item.quantity
                        
                        if total_qty > 0:
                            product.price_cost = (current_value + purchase_value) / total_qty
                        
                        product.stock_quantity += item.quantity
                        
                        stock_log = StockLog(
                            product_id=item.product_id,
                            type='入库',
                            quantity=item.quantity,
                            cost_price=item.price,
                            related_order_no=purchase_order.order_no,
                            operator=operator,
                            remark='采购入库'
                        )
                        self.db.add(stock_log)
                
                purchase_order.status = '已完成'
                purchase_order.finish_time = now
                self.db.commit()
                logger.info(f"采购订单入库完成: {purchase_order.order_no}")
                publish_event('purchase_received', purchase_id=purchase_id)
                return True

            elif purchase_order.order_type == '退货':
                if purchase_order.status != '待退货':
                    raise ValueError("退货订单状态不正确")
                
                # 检查库存是否足够
                for item in purchase_order.items:
                    product = self.db.get(Product, item.product_id)
                    if not product or product.stock_quantity < item.quantity:
                        raise ValueError(f"商品 {product.name if product else item.product_id} 库存不足，无法退货")
                
                for item in purchase_order.items:
                    product = self.db.get(Product, item.product_id)
                    if product:
                        # 退货不影响加权平均成本，除非退货价格不同于当前成本
                        # 简化逻辑：退货时保持单位成本不变，直接扣减数量
                        # 或者：如果认为退货是撤销之前的采购，可以不调整成本价，也可以调整。
                        # 通常：移动加权平均下，出库（退货）按当前成本结转，不影响剩余库存单位成本。
                        # 但如果是按原价退货，且原价 != 当前成本，则剩余库存的总价值会发生非线性变化，从而影响单位成本。
                        # 这里选择：简单扣减数量，不调整单位成本（假设差异计入损益或忽略）。
                        # 或者：如果必须精确，退货应视为负入库。
                        # current_value = product.stock_quantity * product.price_cost
                        # return_value = item.quantity * item.price
                        # remaining_value = current_value - return_value
                        # remaining_qty = product.stock_quantity - item.quantity
                        # if remaining_qty > 0: product.price_cost = remaining_value / remaining_qty
                        
                        # 为了稳健，暂不调整单位成本，避免因价格波动导致成本异常。
                        
                        product.stock_quantity -= item.quantity
                        
                        stock_log = StockLog(
                            product_id=item.product_id,
                            type='采购退货',
                            quantity=-item.quantity,
                            cost_price=item.price,
                            related_order_no=purchase_order.order_no,
                            operator=operator,
                            remark=f'采购退货 (原单:{purchase_order.ref_order_no or "无"})'
                        )
                        self.db.add(stock_log)
                
                purchase_order.status = '已完成'
                purchase_order.finish_time = now
                self.db.commit()
                logger.info(f"采购退货完成: {purchase_order.order_no}")
                publish_event('purchase_returned', purchase_id=purchase_id)
                return True
            
            else:
                raise ValueError(f"未知的订单类型: {purchase_order.order_type}")
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"处理采购订单失败: {e}")
            raise
