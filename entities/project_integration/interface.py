from abc import ABC, abstractmethod
from typing import Any

from common.interfaces import Interface


class ProjectIntegrationInterface(Interface, ABC):
    """Operation interface for creating entities"""

    @abstractmethod
    def stage(self, **kwargs) -> Any:
        pass

    @abstractmethod
    def publish(self, **kwargs) -> Any:
        pass