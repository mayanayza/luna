"""
User interaction abstraction for CLI and other interfaces.
"""
import logging
from abc import ABC, abstractmethod
from typing import Any, Type

from src.script.api._form import FormBuilder
from src.script.api._validation import InputValidator
from src.script.constants import EntityType


class UIContext:
    def __init__(self, registry_manager):
        self._registry_manager = registry_manager
        self._entity_type = None
        self._current_entity_registry = None

    @property
    def entity_type(self):
        return self._entity_type

    @entity_type.setter
    def entity_type(self, val):
        self._entity_type = val
        self._current_entity_registry = self._registry_manager.get_by_name(self._entity_type)

    @property
    def current_entity_registry(self):
        return self._current_entity_registry    
    

class UserInterface(ABC):
    """Abstract base class for user interaction."""
    
    def __init__(self, registry_manager, form_builder_cls: Type[FormBuilder]):
        """
        Initialize the UserInteraction.
        
        Args:
            logger: Logger instance for logging messages
        """
        self.logger = logging.getLogger(__name__)

        self.context = UIContext(registry_manager)
        self.validator = InputValidator(self.context)
        self.form_builder = form_builder_cls(self.validator, registry_manager.get_by_name(EntityType.HANDLER))

    @abstractmethod
    def confirm(self, message: str, default: bool = False) -> bool:
        """
        Ask the user for confirmation.
        
        Args:
            message: Confirmation message to display
            default: Default value if the user provides no input
            
        Returns:
            bool: True if confirmed, False otherwise
        """
        pass
    
    # ---- Output Methods ----
    
    @abstractmethod
    def respond(self, message: str, level: str = "info") -> None:
        """
        Display a message to the user.
        
        Args:
            message: Message to display
            level: Message level (info, warning, error)
        """
        pass
    
    @abstractmethod
    def help(self, parser: Any) -> None:
        """
        Display help information.
        
        Args:
            parser: ArgumentParser instance or other help object
        """
        pass