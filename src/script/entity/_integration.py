from abc import abstractmethod
from typing import TYPE_CHECKING, List

from src.script.constants import EntityType
from src.script.entity._base import CreatableEntity
from src.script.entity._project import Project
from src.script.templates.processor import TemplateProcessor

if TYPE_CHECKING:
    pass

class Integration(CreatableEntity):
    def __init__(self, registry, integration_type, **kwargs):

        self._integration_type = integration_type

        self._db_fields = {
            'integration_type': integration_type
        }

        if not hasattr(self, '_project_integration_config_fields'):
            self._project_integration_config_fields: List = []
        
        # Set up templates
        self.tp = TemplateProcessor()
        
        # Initialize environment and API config for integration
        # self._init_env_vars()
        self._init_apis()

        super().__init__(registry, EntityType.INTEGRATION, **kwargs)
        
    def _init_apis(self) -> None:
        for name, api_config in self._apis.items():
            if callable(api_config):
                api_config()

    @abstractmethod
    def setup(self, project: Project, **kwargs):
        pass

    @abstractmethod
    def remove(self, project: Project, **kwargs):
        pass

    @abstractmethod
    def rename(self, project: Project, **kwargs):
        pass