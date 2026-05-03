import hashlib
from shared.models.user import User
from datetime import datetime

class AuthService:
    def __init__(self, db_or_session):
        self.db_or_session = db_or_session
    
    def hash_password(self, password):
        return hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    def verify_password(self, password, password_hash):
        return self.hash_password(password) == password_hash
    
    def _get_db(self):
        # 检查是否是可调用的（db_session函数）
        if callable(self.db_or_session):
            return self.db_or_session()
        return self.db_or_session
    
    def authenticate(self, username, password):
        db = self._get_db()
        try:
            # 尝试使用with语句（如果是上下文管理器）
            with db as session:
                return self._authenticate_with_session(session, username, password)
        except:
            # 如果不是上下文管理器，直接使用
            try:
                return self._authenticate_with_session(db, username, password)
            finally:
                # 如果是通过调用db_session()获取的会话，确保关闭
                if hasattr(db, 'close'):
                    db.close()
    
    def _authenticate_with_session(self, db, username, password):
        user = db.query(User).filter(User.username == username).first()
        if user and self.verify_password(password, user.password_hash):
            user.last_login = datetime.now()
            db.commit()
            # 创建一个简单的用户对象，包含需要的属性
            class SimpleUser:
                def __init__(self, user):
                    self.id = user.id
                    self.username = user.username
                    self.real_name = user.real_name
                    self.role = user.role
                    self.create_time = getattr(user, 'create_time', None)
                    self.update_time = getattr(user, 'update_time', None)
                    self.last_login = getattr(user, 'last_login', None)
                    self.status = getattr(user, 'status', '正常')
            return SimpleUser(user)
        return None
    
    def create_user(self, username, password, role='收银员', real_name=None):
        db = self._get_db()
        try:
            # 尝试使用with语句（如果是上下文管理器）
            with db as session:
                return self._create_user_with_session(session, username, password, role, real_name)
        except:
            # 如果不是上下文管理器，直接使用
            try:
                return self._create_user_with_session(db, username, password, role, real_name)
            finally:
                # 如果是通过调用db_session()获取的会话，确保关闭
                if hasattr(db, 'close'):
                    db.close()
    
    def _create_user_with_session(self, db, username, password, role, real_name):
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            raise ValueError(f"用户名 {username} 已存在")
        
        user = User(
            username=username,
            password_hash=self.hash_password(password),
            role=role,
            real_name=real_name
        )
        db.add(user)
        db.commit()
        return user
    
    def update_password(self, user_id, new_password):
        db = self._get_db()
        try:
            # 尝试使用with语句（如果是上下文管理器）
            with db as session:
                return self._update_password_with_session(session, user_id, new_password)
        except:
            # 如果不是上下文管理器，直接使用
            try:
                return self._update_password_with_session(db, user_id, new_password)
            finally:
                # 如果是通过调用db_session()获取的会话，确保关闭
                if hasattr(db, 'close'):
                    db.close()
    
    def _update_password_with_session(self, db, user_id, new_password):
        user = db.get(User, user_id)
        if user:
            user.password_hash = self.hash_password(new_password)
            db.commit()
            return True
        return False
    
    def get_user(self, user_id):
        db = self._get_db()
        try:
            # 尝试使用with语句（如果是上下文管理器）
            with db as session:
                return session.get(User, user_id)
        except:
            # 如果不是上下文管理器，直接使用
            try:
                return db.get(User, user_id)
            finally:
                # 如果是通过调用db_session()获取的会话，确保关闭
                if hasattr(db, 'close'):
                    db.close()
    
    def list_users(self):
        db = self._get_db()
        try:
            # 尝试使用with语句（如果是上下文管理器）
            with db as session:
                return session.query(User).all()
        except:
            # 如果不是上下文管理器，直接使用
            try:
                return db.query(User).all()
            finally:
                # 如果是通过调用db_session()获取的会话，确保关闭
                if hasattr(db, 'close'):
                    db.close()
