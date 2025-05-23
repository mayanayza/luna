from abc import abstractmethod
from typing import TYPE_CHECKING

from src.script.entity._base import StorableEntity
from src.script.entity._project import Project
from src.script.templates.processor import TemplateProcessor

if TYPE_CHECKING:
    pass

class Integration(StorableEntity):
    def __init__(self, registry, name, emoji, title, **kwargs):

        kwargs['name'] = name
        super().__init__(registry, **kwargs)

        self._emoji = emoji
        self._title = title

        self._db_fields = {
            'emoji': self._emoji,
            'title': self._title,
        }

        # Set up templates
        self.tp = TemplateProcessor()
        
        # Initialize environment and API config for integration
        # self._init_env_vars()
        self._init_apis()
        
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