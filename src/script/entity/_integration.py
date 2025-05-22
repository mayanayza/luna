import os
from abc import abstractmethod
from typing import TYPE_CHECKING

from dotenv import load_dotenv
from src.script.entity._base import ModuleEntity
from src.script.entity._project import Project
from src.script.templates.processor import TemplateProcessor

if TYPE_CHECKING:
    pass

load_dotenv()

class Integration(ModuleEntity):
    def __init__(self, registry, config):        
        # Initialize base class
        super().__init__(registry, config['name'])

        self._config = config
        
        # Set up templates
        self.tp = TemplateProcessor()
        
        # Initialize environment and API config for integration
        self._init_env_vars()
        self._init_apis()

    @property
    def config(self):
        return self._config
    

    @property
    def db_additional_fields(self):
        return {
            'config': self._config
        }
    
    def _init_env_vars(self) -> None:
        self.env = {}
        for name, env_config in self._config.get('env',{}).items():
            self.env[name] = os.environ.get(env_config)

    def _init_apis(self) -> None:
        for name, api_config in self._config.get('apis', {}).items():
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