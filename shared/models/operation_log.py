from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel
import datetime

class OperationLog(BaseModel):
    __tablename__ = 'operation_logs'
    
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    action = Column(String(100))
    detail = Column(Text)
    ip = Column(String(50))
    
    user = relationship("User")
    
    def __repr__(self):
        return f"<OperationLog {self.action}>"
