MODULE_INFO = {
    "name": "member",
    "version": "1.0.0",
    "description": "会员管理模块",
    "dependencies": ["shared.models"],
    "entry_points": {
        "controllers": "MemberController"
    }
}

def init_module():
    from .controllers import MemberController
    from core.service_registry import register_service
    
    register_service("member_controller", MemberController)

def shutdown_module():
    from core.service_registry import unregister_service
    unregister_service("member_controller")
