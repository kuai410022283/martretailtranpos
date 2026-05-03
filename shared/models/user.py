from sqlalchemy import Column, Integer, String, DateTime
from .base import BaseModel

class User(BaseModel):
    __tablename__ = 'users'
    
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    role = Column(String(20), default='收银员')
    real_name = Column(String(50))
    last_login = Column(DateTime, nullable=True)
    status = Column(String(20), default='正常')
    
    def __repr__(self):
        return f"<User {self.username}>"
