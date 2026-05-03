MODULE_INFO = {
    "name": "purchase",
    "version": "1.0.0",
    "description": "采购管理模块",
    "dependencies": ["shared.models", "product"],
    "entry_points": {
        "controllers": "PurchaseController"
    }
}

def init_module():
    from .controllers import PurchaseController
    from core.service_registry import register_service
    
    register_service("purchase_controller", PurchaseController)

def shutdown_module():
    from core.service_registry import unregister_service
    unregister_service("purchase_controller")
