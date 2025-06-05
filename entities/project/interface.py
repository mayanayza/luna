from abc import ABC, abstractmethod
from typing import Any

from common.interfaces import Interface


class ProjectInterface(Interface, ABC):
    """Operation interface for creating entities"""

    @abstractmethod
    def add_integration(self, **kwargs) -> Any:
        pass

    @abstractmethod
    def remove_integration(self, **kwargs) -> Any:
        pass

    @abstractmethod
    def list_integrations(self, **kwargs) -> Any:
        pass