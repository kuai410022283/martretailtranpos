import os
import importlib
from core.logger import logger
from core.exceptions import ModuleLoadError, DependencyError

class ModuleLoader:
    def __init__(self):
        self.modules = {}
        self.module_info = {}
        self.dependency_graph = {}
        self.loaded_modules = []
        self.sorted_modules = []
    
    def discover_modules(self):
        modules_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'modules')
        
        if not os.path.exists(modules_dir):
            logger.warning(f"模块目录不存在: {modules_dir}")
            return
        
        for module_name in os.listdir(modules_dir):
            module_path = os.path.join(modules_dir, module_name)
            
            if not os.path.isdir(module_path):
                continue
            
            init_file = os.path.join(module_path, '__init__.py')
            if not os.path.exists(init_file):
                continue
            
            try:
                module = importlib.import_module(f"modules.{module_name}")
                
                if hasattr(module, 'MODULE_INFO'):
                    self.modules[module_name] = module
                    self.module_info[module_name] = module.MODULE_INFO
                    self.dependency_graph[module_name] = module.MODULE_INFO.get('dependencies', [])
                    logger.info(f"发现模块: {module_name} v{module.MODULE_INFO.get('version', 'unknown')}")
                else:
                    logger.debug(f"跳过模块 {module_name}（缺少 MODULE_INFO）")
            
            except Exception as e:
                logger.error(f"加载模块 {module_name} 失败: {e}", exc_info=True)
    
    def resolve_dependencies(self):
        sorted_modules = []
        visited = set()
        temp = set()
        
        def visit(module_name):
            if module_name in temp:
                raise DependencyError(f"发现循环依赖: {module_name}")
            if module_name not in visited:
                temp.add(module_name)
                
                for dep in self.dependency_graph.get(module_name, []):
                    if dep in self.modules:
                        visit(dep)
                
                temp.remove(module_name)
                visited.add(module_name)
                sorted_modules.append(module_name)
        
        for module_name in self.modules:
            if module_name not in visited:
                visit(module_name)
        
        self.sorted_modules = sorted_modules
        logger.info(f"模块加载顺序: {', '.join(self.sorted_modules)}")
    
    def load_modules(self):
        for module_name in self.sorted_modules:
            module = self.modules[module_name]
            
            try:
                if hasattr(module, 'init_module'):
                    module.init_module()
                    logger.info(f"已加载模块: {module_name}")
                else:
                    logger.debug(f"模块 {module_name} 无 init_module，跳过初始化")
                
                self.loaded_modules.append(module_name)
            
            except Exception as e:
                logger.error(f"初始化模块 {module_name} 失败: {e}", exc_info=True)
                raise ModuleLoadError(f"模块 {module_name} 初始化失败") from e
    
    def unload_modules(self):
        for module_name in reversed(self.loaded_modules):
            module = self.modules[module_name]
            
            try:
                if hasattr(module, 'shutdown_module'):
                    module.shutdown_module()
                    logger.info(f"已卸载模块: {module_name}")
            
            except Exception as e:
                logger.error(f"卸载模块 {module_name} 失败: {e}", exc_info=True)
    
    def get_module(self, module_name):
        return self.modules.get(module_name)
    
    def list_modules(self):
        return list(self.modules.keys())
    
    def is_loaded(self, module_name):
        return module_name in self.loaded_modules
