class ServiceRegistry:
    def __init__(self):
        self._services = {}
    
    def register(self, service_id, service):
        self._services[service_id] = service
    
    def unregister(self, service_id):
        if service_id in self._services:
            del self._services[service_id]
    
    def get(self, service_id):
        if service_id not in self._services:
            raise ValueError(f"Service {service_id} not found")
        return self._services[service_id]
    
    def has(self, service_id):
        return service_id in self._services
    
    def list_services(self):
        return list(self._services.keys())

service_registry = ServiceRegistry()

def register_service(service_id, service):
    service_registry.register(service_id, service)

def unregister_service(service_id):
    service_registry.unregister(service_id)

def get_service(service_id):
    return service_registry.get(service_id)

def has_service(service_id):
    return service_registry.has(service_id)

def list_services():
    return service_registry.list_services()
