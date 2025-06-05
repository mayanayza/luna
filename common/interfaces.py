from abc import ABC, abstractmethod
from typing import List, Any, Dict, Type, re


class Interface(ABC):
    """Used to ensure that service and api implement the same methods. Only one capability per entity can implement a given interface."""
    pass

class ListableInterface(Interface, ABC):
    """Operation interface for listing entities"""

    @abstractmethod
    def list(self, sort_by: str = "name", filter_name: str = None) -> List[Any]:
        pass

    @abstractmethod
    def details(self, entity) -> Dict[str, Any]:
        pass

class CreatableInterface(Interface, ABC):
    """Operation interface for creating entities"""

    @abstractmethod
    def create(self, **kwargs) -> Any:
        pass


class DeletableInterface(Interface, ABC):
    """Operation interface for deleting entities"""

    @abstractmethod
    def delete(self, entity) -> bool:
        pass


class RenamableInterface(Interface, ABC):
    """Operation interface for renaming entities"""

    @abstractmethod
    def rename(self, entity, new_name: str, **kwargs) -> Dict[str, str]:
        pass


class EditableInterface(Interface, ABC):
    """Operation interface for editing entity configuration"""

    @abstractmethod
    def edit(self, entity, **config_updates) -> Any:
        pass


class UserNameableInterface(Interface, ABC):
    """Operation interface for user-nameable entities"""

    @staticmethod
    def is_valid_name(name: str, max_length: int = 255) -> tuple[bool, str]:
        """
        Validate a name string for general use in applications.
        Returns (is_valid, error_message)
        """
        if not name:
            return False, "Name cannot be empty"

        # Trim and check if empty after trimming
        trimmed = name.strip()
        if not trimmed:
            return False, "Name cannot be only whitespace"

        # Check length
        if len(trimmed) > max_length:
            return False, f"Name too long (max {max_length} characters)"

        # Check for control characters (except normal whitespace)
        if re.search(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', trimmed):
            return False, "Name contains invalid control characters"

        # Optional: Check for potentially problematic characters
        # This is very permissive - only blocks the most problematic ones
        dangerous_chars = ['<', '>', '"', '|', '\0', '/', '\\', ':', '*', '?']
        if any(char in trimmed for char in dangerous_chars):
            return False, "Name contains reserved characters"

        return True, ""

class ImplementationDiscoveryInterface(Interface, ABC):
    """Operation interface for implementation-based entities"""

    @abstractmethod
    def list_implementations(self) -> List[str]:
        pass

    @abstractmethod
    def is_implementation(self, implementation_name: str) -> bool:
        pass
