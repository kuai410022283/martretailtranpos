MODULE_INFO = {
    "name": "sale",
    "version": "1.0.0",
    "description": "销售管理模块",
    "dependencies": ["shared.models", "pos"],
    "entry_points": {
        "controllers": "SaleController"
    }
}

def init_module():
    from .controllers import SaleController
    from core.service_registry import register_service
    
    register_service("sale_controller", SaleController)

def shutdown_module():
    from core.service_registry import unregister_service
    unregister_service("sale_controller")
