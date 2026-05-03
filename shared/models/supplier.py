from sqlalchemy import Column, Integer, String, Text
from .base import BaseModel

class Supplier(BaseModel):
    __tablename__ = 'suppliers'
    
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    contact = Column(String(50))
    phone = Column(String(20))
    address = Column(String(200))
    remark = Column(Text)
    
    def __repr__(self):
        return f"<Supplier {self.name}>"
