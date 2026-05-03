MODULE_INFO = {
    "name": "finance",
    "version": "1.0.0",
    "description": "财务管理模块",
    "dependencies": ["shared.models", "sale"],
    "entry_points": {
        "controllers": "FinanceController"
    }
}

def init_module():
    from .controllers import FinanceController
    from core.service_registry import register_service
    
    register_service("finance_controller", FinanceController)

def shutdown_module():
    from core.service_registry import unregister_service
    unregister_service("finance_controller")
