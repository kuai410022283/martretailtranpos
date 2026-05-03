MODULE_INFO = {
    "name": "stock",
    "version": "1.0.0",
    "description": "库存管理模块",
    "dependencies": ["shared.models", "product"],
    "entry_points": {
        "controllers": "StockController"
    }
}

def init_module():
    from .controllers import StockController
    from core.service_registry import register_service
    
    register_service("stock_controller", StockController)

def shutdown_module():
    from core.service_registry import unregister_service
    unregister_service("stock_controller")
