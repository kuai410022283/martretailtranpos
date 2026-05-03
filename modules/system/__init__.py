MODULE_INFO = {
    "name": "system",
    "version": "1.0.0",
    "description": "系统管理模块",
    "dependencies": ["shared.models"],
    "entry_points": {
        "controllers": "SystemController"
    }
}

def init_module():
    from .controllers import SystemController
    from core.service_registry import register_service
    
    register_service("system_controller", SystemController)

def shutdown_module():
    from core.service_registry import unregister_service
    unregister_service("system_controller")
