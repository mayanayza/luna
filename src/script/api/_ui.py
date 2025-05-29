"""
User interaction abstraction for CLI and other interfaces.
"""
import logging
from abc import ABC, abstractmethod
from typing import Any


class UserInterface(ABC):
    """Abstract base class for user interaction."""
    
    def __init__(self):
        """
        Initialize the UserInteraction.
        
        Args:
            logger: Logger instance for logging messages
        """
        self.logger = logging.getLogger(self.__class__.__name__)

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