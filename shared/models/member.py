from sqlalchemy import Column, Integer, String, Float, DateTime
from .base import BaseModel

class Member(BaseModel):
    __tablename__ = 'members'
    
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(50))
    phone = Column(String(20), unique=True)
    grade = Column(String(20), default='普通会员')
    points = Column(Integer, default=0)
    balance = Column(Float, default=0.0)
    remark = Column(String(200))
    
    def __repr__(self):
        return f"<Member {self.name}>"
