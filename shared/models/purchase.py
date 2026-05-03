from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .base import BaseModel
import datetime

class PurchaseOrder(BaseModel):
    __tablename__ = 'purchase_orders'
    
    order_no = Column(String(20), unique=True, nullable=False)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'))
    order_type = Column(String(20), default='采购')  # 采购, 退货
    ref_order_no = Column(String(20), nullable=True)  # 关联原单号
    total_amount = Column(Float, default=0.0)
    status = Column(String(20), default='待入库')
    finish_time = Column(DateTime, nullable=True)
    remark = Column(String(200))
    
    supplier = relationship("Supplier")
    items = relationship("PurchaseItem", back_populates="purchase", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<PurchaseOrder {self.order_no}>"

class PurchaseItem(BaseModel):
    __tablename__ = 'purchase_items'
    
    purchase_id = Column(Integer, ForeignKey('purchase_orders.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    quantity = Column(Float)
    price = Column(Float)
    amount = Column(Float)
    
    purchase = relationship("PurchaseOrder", back_populates="items")
    product = relationship("Product")
    
    def __repr__(self):
        return f"<PurchaseItem {self.product.name} x {self.quantity}>"
