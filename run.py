#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import load_config
from core.database import init_database
from core.logger import logger
from core.module_loader import ModuleLoader
from core.event_bus import publish_event
from shared.services.auth_service import AuthService

def init_default_data(db_session):
    from shared.models.user import User
    from shared.models.product import Category
    
    with db_session() as db:
        existing_admin = db.query(User).filter(User.username == 'admin').first()
        if not existing_admin:
            auth_service = AuthService(db)
            admin = auth_service.create_user(
                username='admin',
                password='admin123',
                role='管理员',
                real_name='系统管理员'
            )
            logger.info(f"创建默认管理员账户: admin / admin123")
            
        if db.query(Category).count() == 0:
            categories = ["饮料", "食品", "日用品", "文具", "电子产品", "服装", "生鲜", "熟食"]
            for name in categories:
                db.add(Category(name=name))
            logger.info("初始化默认商品分类")

def main():
    try:
        config = load_config()
        logger.setup(config.get('logging', {}))
        logger.info("=" * 50)
        logger.info("MartRetailTranPOS 启动中...")
        
        db_engine = init_database(config.get('database'))
        logger.info("数据库初始化完成")
        
        from core.database import db_session
        init_default_data(db_session)
        
        loader = ModuleLoader()
        loader.discover_modules()
        loader.resolve_dependencies()
        loader.load_modules()
        logger.info("模块加载完成")
        
        publish_event('app_started')
        logger.info("系统启动成功")
        
        show_login_window(db_session)
        
    except Exception as e:
        logger.error(f"系统启动失败: {e}", exc_info=True)
        sys.exit(1)

def show_login_window(db_session):
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import Qt
        from shared.views.login_window import LoginWindow
        
        # 启用高DPI缩放
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
        
        app = QApplication(sys.argv)
        
        # 设置默认字体
        from PyQt5.QtGui import QFont, QIcon
        font = QFont("Segoe UI Variable Text", 9)
        font.setStyleStrategy(QFont.PreferAntialias)
        app.setFont(font)
        
        app.setApplicationName("MartRetailTranPOS")
        
        # 设置应用图标
        # 尝试按优先级加载图标
        base_dir = os.path.dirname(os.path.abspath(__file__))
        icon_candidates = [
            os.path.join(base_dir, 'resources', 'icons', 'app.ico'),
            os.path.join(base_dir, 'resources', 'icon.png'),
            os.path.join(base_dir, 'resources', 'icon.svg')
        ]
        
        icon_set = False
        for icon_path in icon_candidates:
            if os.path.exists(icon_path):
                app.setWindowIcon(QIcon(icon_path))
                logger.info(f"已设置应用图标: {icon_path}")
                icon_set = True
                break
        
        if not icon_set:
            logger.warning("未找到应用图标文件")
        
        login_window = LoginWindow(db_session)
        login_window.show()
        
        sys.exit(app.exec_())
    except ImportError as e:
        logger.error(f"导入 PyQt5 失败: {e}")
        logger.info("请先安装依赖: pip install -r requirements.txt")
        sys.exit(1)

if __name__ == '__main__':
    main()
