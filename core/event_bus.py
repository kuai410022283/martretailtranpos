class EventBus:
    def __init__(self):
        self._subscribers = {}
    
    def subscribe(self, event_name, callback):
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        self._subscribers[event_name].append(callback)
    
    def unsubscribe(self, event_name, callback):
        if event_name in self._subscribers:
            if callback in self._subscribers[event_name]:
                self._subscribers[event_name].remove(callback)
            if not self._subscribers[event_name]:
                del self._subscribers[event_name]
    
    def publish(self, event_name, **kwargs):
        if event_name in self._subscribers:
            for callback in self._subscribers[event_name]:
                try:
                    callback(**kwargs)
                except Exception as e:
                    from core.logger import logger
                    logger.error(f"事件处理错误 {event_name}: {e}", exc_info=True)

event_bus = EventBus()

def subscribe_event(event_name, callback):
    event_bus.subscribe(event_name, callback)

def unsubscribe_event(event_name, callback):
    event_bus.unsubscribe(event_name, callback)

def publish_event(event_name, **kwargs):
    event_bus.publish(event_name, **kwargs)
