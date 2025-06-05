from abc import ABC, abstractmethod
from typing import Any

from common.interfaces import Interface


class DatabaseInterface(Interface, ABC):
    """Operation interface for creating entities"""

    @abstractmethod
    def clear(self, **kwargs) -> Any:
        pass

    @abstractmethod
    def test(self, **kwargs) -> Any:
        pass