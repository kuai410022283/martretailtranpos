MODULE_INFO = {
    "name": "product",
    "version": "1.0.0",
    "description": "商品管理模块",
    "dependencies": ["shared.models", "shared.utils", "shared.services"],
    "entry_points": {
        "controllers": "ProductController"
    }
}

def init_module():
    from .controllers import ProductController
    from core.service_registry import register_service
    
    register_service("product_controller", ProductController)

def shutdown_module():
    from core.service_registry import unregister_service
    unregister_service("product_controller")
