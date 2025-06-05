from abc import abstractmethod
from typing import Dict

from entities.project import Project
from entities.base import Entity

class IntegrationBase(Entity):

    def __init__(self, registry, **kwargs):
        super().__init__(registry, **kwargs)
        # Pertains to a project's use of a given integration instance
        self._project_integration_config_fields: Dict = {}

    @abstractmethod
    def setup(self, project: Project, **kwargs) -> None:
        """Setup integration for a project"""
        pass

    @abstractmethod
    def remove(self, project: Project, **kwargs) -> None:
        """Remove integration from a project"""
        pass

    @abstractmethod
    def rename(self, project: Project, old_name, **kwargs) -> None:
        """Handle project rename for this integration"""
        pass

    @abstractmethod
    def publish(self, project: Project, **kwargs) -> None:
        """Publish project through this integration"""
        pass

    @abstractmethod
    def stage(self, project: Project, **kwargs) -> None:
        """Stage project through this integration"""
        pass

    