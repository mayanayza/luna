
from abc import abstractmethod
from typing import Any, Callable, List, Type

from src.script.constants import Command, EntityType
from src.script.entity._base import ModuleEntity


class Handler(ModuleEntity):
    def __init__(self, registry, handler_func: Callable, **kwargs):
        super().__init__(registry, EntityType.HANDLER, **kwargs)
        self.handler_func = handler_func

        return self
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """Execute the handler logic"""
        try:
            return self.handler_func(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"Handler {self.name} failed: {e}")
            raise
    
    def __call__(self, *args, **kwargs) -> Any:
        """Make handler callable"""
        return self.execute(*args, **kwargs)

class SystemFormHandler(Handler):
    """System-defined form handlers"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def execute(self, *args, **kwargs) -> Any:
        """Execute system handler function"""
        super().execute(*args, **kwargs)

class UserFormHandler(Handler):
    """User-defined form handlers (configured by users)"""
    def __init__(self, name: str, **kwargs):
        super().__init__(**kwargs)
    
    def execute(self, *args, **kwargs) -> Any:
        """Execute user-defined handler function"""
        super().execute(*args, **kwargs)

class CommandArgument:
    def __init__(self, name, short, type: Type[Any], description):
        self._name = name
        self._short = short
        self._type = type
        self._description = description

class CommandHandler(Handler):
    """Handlers for API commands (create project, delete project, etc.)"""
    def __init__(self, description:str, command: Command, args: List[CommandArgument], requires_auth: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.requires_auth = requires_auth
        self.command = command
        self.description = description
    
    def execute(self, *args, **kwargs) -> Any:
        """Execute command handler function"""
        super().execute(*args, **kwargs)
    
    def can_execute(self, user_context=None) -> bool:
        """Check if command can be executed (override for custom auth logic)"""
        if self.requires_auth and not user_context:
            return False
        return True