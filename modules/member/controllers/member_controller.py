from sqlalchemy.orm import Session
from shared.models.member import Member
from shared.utils.order_generator import generate_member_no
from core.logger import logger
from core.event_bus import publish_event

class MemberController:
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def create_member(self, **kwargs):
        if 'code' not in kwargs or not kwargs['code']:
            kwargs['code'] = generate_member_no()
        
        member = Member(**kwargs)
        self.db.add(member)
        self.db.commit()
        logger.info(f"创建会员: {member.code} - {member.name}")
        publish_event('member_created', member_id=member.id)
        return member
    
    def get_member(self, member_id):
        return self.db.get(Member, member_id)
    
    def get_member_by_code(self, code):
        return self.db.query(Member).filter(Member.code == code).first()
    
    def get_member_by_phone(self, phone):
        return self.db.query(Member).filter(Member.phone == phone).first()
    
    def list_members(self, keyword=None, grade=None):
        query = self.db.query(Member)
        
        if keyword:
            query = query.filter(
                (Member.name.contains(keyword)) | 
                (Member.code.contains(keyword)) |
                (Member.phone.contains(keyword))
            )
        if grade:
            query = query.filter(Member.grade == grade)
        
        return query.order_by(Member.create_time.desc()).all()
    
    def update_member(self, member_id, **kwargs):
        member = self.get_member(member_id)
        if not member:
            return None
        
        for key, value in kwargs.items():
            if hasattr(member, key):
                setattr(member, key, value)
        
        self.db.commit()
        logger.info(f"更新会员: {member.code} - {member.name}")
        return member
    
    def add_points(self, member_id, points, remark=""):
        member = self.get_member(member_id)
        if not member:
            raise ValueError("会员不存在")
        
        member.points += points
        self.db.commit()
        logger.info(f"会员积分变动: {member.name} +{points}")
        return True
    
    def deduct_points(self, member_id, points, remark=""):
        member = self.get_member(member_id)
        if not member:
            raise ValueError("会员不存在")
        
        if member.points < points:
            raise ValueError("积分不足")
        
        member.points -= points
        self.db.commit()
        logger.info(f"会员积分变动: {member.name} -{points}")
        return True
    
    def recharge(self, member_id, amount, remark=""):
        member = self.get_member(member_id)
        if not member:
            raise ValueError("会员不存在")
        
        member.balance += amount
        self.db.commit()
        logger.info(f"会员充值: {member.name} +{amount}")
        return True
    
    def consume_balance(self, member_id, amount, remark=""):
        member = self.get_member(member_id)
        if not member:
            raise ValueError("会员不存在")
        
        if member.balance < amount:
            raise ValueError("余额不足")
        
        member.balance -= amount
        self.db.commit()
        logger.info(f"会员余额消费: {member.name} -{amount}")
        return True
    
    def delete_member(self, member_id):
        member = self.get_member(member_id)
        if not member:
            return False
        
        self.db.delete(member)
        self.db.commit()
        logger.info(f"删除会员: {member.code} - {member.name}")
        return True
