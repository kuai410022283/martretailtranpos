from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import contextmanager
import os

Base = declarative_base()

db_engine = None
db_session = None

def init_database(config=None):
    global db_engine, db_session
    
    if config is None:
        config = {
            'database_type': 'sqlite',
            'database_path': 'data/mrtpos.db'
        }
    
    database_type = config.get('database_type', 'sqlite')
    
    if database_type == 'sqlite':
        db_path = config.get('database_path', 'data/mrtpos.db')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        database_url = f'sqlite:///{db_path}'
    elif database_type == 'postgresql':
        database_url = (
            f"postgresql://{config.get('username')}:{config.get('password')}"
            f"@{config.get('host')}:{config.get('port')}/{config.get('database')}"
        )
    elif database_type == 'mysql':
        database_url = (
            f"mysql+pymysql://{config.get('username')}:{config.get('password')}"
            f"@{config.get('host')}:{config.get('port')}/{config.get('database')}"
        )
    else:
        raise ValueError(f"不支持的数据库类型: {database_type}")
    
    # 增加连接池大小，解决连接超时问题
    db_engine = create_engine(
        database_url, 
        echo=False,
        pool_size=20,            # 连接池大小
        max_overflow=30,         # 最大溢出连接数
        pool_timeout=60,         # 连接超时时间（秒）
        pool_recycle=3600,       # 连接回收时间（秒）
        pool_pre_ping=True        # 连接前ping测试
    )
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    
    @contextmanager
    def get_db():
        db = SessionLocal()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
    
    globals()['db_session'] = get_db
    
    # 导入所有模型，确保SQLAlchemy知道要创建哪些表
    from shared.models.user import User
    from shared.models.product import Product
    from shared.models.supplier import Supplier
    from shared.models.purchase import PurchaseOrder, PurchaseItem
    from shared.models.sale import SaleOrder, SaleItem
    from shared.models.stock_log import StockLog
    from shared.models.member import Member
    from shared.models.operation_log import OperationLog
    
    from shared.models.base import Base
    Base.metadata.create_all(bind=db_engine)
    
    return db_engine

def create_tables():
    if db_engine:
        Base.metadata.create_all(bind=db_engine)
