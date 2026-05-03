from sqlalchemy.orm import Session
from shared.models.user import User
from shared.models.operation_log import OperationLog
from core.logger import logger
from core.config import load_config
import hashlib
import json
import os
import shutil
from datetime import datetime
import configparser

class SystemController:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.config_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'config.ini')
        self.config = load_config(self.config_file)
    
    def hash_password(self, password):
        return hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    def create_user(self, username, password, **kwargs):
        if self.db.query(User).filter(User.username == username).first():
            raise ValueError("用户名已存在")
        
        user = User(
            username=username,
            password=self.hash_password(password),
            **kwargs
        )
        self.db.add(user)
        self.db.commit()
        logger.info(f"创建用户: {username}")
        return user
    
    def get_user(self, user_id):
        return self.db.get(User, user_id)
    
    def get_user_by_username(self, username):
        return self.db.query(User).filter(User.username == username).first()
    
    def list_users(self):
        return self.db.query(User).order_by(User.create_time.desc()).all()
    
    def update_user(self, user_id, **kwargs):
        user = self.get_user(user_id)
        if not user:
            return None
        
        if 'password' in kwargs and kwargs['password']:
            kwargs['password'] = self.hash_password(kwargs['password'])
        elif 'password' in kwargs:
            del kwargs['password']
        
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        self.db.commit()
        logger.info(f"更新用户: {user.username}")
        return user
    
    def delete_user(self, user_id):
        user = self.get_user(user_id)
        if not user:
            return False
        
        self.db.delete(user)
        self.db.commit()
        logger.info(f"删除用户: {user.username}")
        return True
    
    def list_operation_logs(self, start_date=None, end_date=None, operator=None):
        query = self.db.query(OperationLog)
        
        if start_date:
            query = query.filter(OperationLog.create_time >= start_date)
        if end_date:
            query = query.filter(OperationLog.create_time <= end_date)
        if operator:
            query = query.filter(OperationLog.operator == operator)
        
        return query.order_by(OperationLog.create_time.desc()).all()
    
    def log_operation(self, operator, module, action, content=""):
        log = OperationLog(
            operator=operator,
            module=module,
            action=action,
            content=content
        )
        self.db.add(log)
        self.db.commit()
        return log
    
    def get_config(self, key=None, default=None):
        if key:
            # 处理嵌套键，如 'database.path'
            parts = key.split('.')
            if len(parts) == 2:
                section, option = parts
                return self.config.get(section, {}).get(option, default)
            return default
        return self.config
    
    def set_config(self, key, value):
        # 处理嵌套键，如 'database.path'
        parts = key.split('.')
        if len(parts) == 2:
            section, option = parts
            if section in self.config and isinstance(self.config[section], dict):
                self.config[section][option] = value
                logger.info(f"更新配置: {key} = {value}")
    
    def save_config(self):
        # 保存配置到文件
        config = configparser.ConfigParser()
        for section, options in self.config.items():
            if isinstance(options, dict):
                config.add_section(section)
                for key, value in options.items():
                    config.set(section, key, str(value))
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            config.write(f)
        logger.info("配置已保存")
    
    def backup_database(self, backup_dir='backups'):
        try:
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(backup_dir, f'mart_retail_backup_{timestamp}.db')
            
            # 获取数据库路径
            db_path = self.config.get('database', {}).get('database_path', 'data/mrtpos.db')
            if os.path.exists(db_path):
                shutil.copy2(db_path, backup_file)
                logger.info(f"数据库备份成功: {backup_file}")
                return backup_file
            else:
                # 尝试默认路径
                default_path = 'data/mrtpos.db'
                if os.path.exists(default_path):
                    shutil.copy2(default_path, backup_file)
                    logger.info(f"数据库备份成功 (使用默认路径): {backup_file}")
                    return backup_file
                raise FileNotFoundError(f"数据库文件不存在: {db_path} 和 {default_path}")
        except Exception as e:
            logger.error(f"数据库备份失败: {e}")
            raise
    
    def restore_database(self, backup_file):
        try:
            if not os.path.exists(backup_file):
                raise FileNotFoundError(f"备份文件不存在: {backup_file}")
            
            # 获取数据库路径
            db_path = self.config.get('database', {}).get('database_path', 'data/mrtpos.db')
            # 确保目录存在
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            shutil.copy2(backup_file, db_path)
            logger.info(f"数据库恢复成功: {backup_file}")
            return True
        except Exception as e:
            logger.error(f"数据库恢复失败: {e}")
            raise
    
    def list_backups(self, backup_dir='backups'):
        try:
            if not os.path.exists(backup_dir):
                return []
            
            backups = []
            for filename in os.listdir(backup_dir):
                if filename.startswith('mart_retail_backup_') and filename.endswith('.db'):
                    filepath = os.path.join(backup_dir, filename)
                    stat = os.stat(filepath)
                    backups.append({
                        'filename': filename,
                        'filepath': filepath,
                        'size': stat.st_size,
                        'create_time': datetime.fromtimestamp(stat.st_mtime)
                    })
            
            return sorted(backups, key=lambda x: x['create_time'], reverse=True)
        except Exception as e:
            logger.error(f"获取备份列表失败: {e}")
            return []
    
    def delete_backup(self, backup_file):
        try:
            if os.path.exists(backup_file):
                os.remove(backup_file)
                logger.info(f"删除备份: {backup_file}")
                return True
            return False
        except Exception as e:
            logger.error(f"删除备份失败: {e}")
            raise
