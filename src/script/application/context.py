import logging
import sys
import traceback

import colorlog
from src.script.constants import EntityType
from src.script.registry._manager import RegistryManager
from src.script.registry.api import ApiRegistry
from src.script.registry.db import DatabaseRegistry
from src.script.registry.integration import IntegrationRegistry
from src.script.registry.project import ProjectRegistry
from src.script.registry.projectintegration import ProjectIntegrationRegistry


class ApplicationContext:
    """Central coordination point for application setup"""
    
    def __init__(self):

        self.configure_logging()

        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self.registry_manager = RegistryManager()
        # self.command_dispatcher = CommandDispatcher(self.registry_manager)
        # self.registry_manager.set_command_dispatcher(self.command_dispatcher)
            
    def get_registry(self, registry_name):
        return self.registry_manager.get_by_name(registry_name)

    def register_registry(self, registry_name, registry_class, **init_kwargs):
        """Create and register a registry of the given class."""
        self.logger.info(f"Initializing {registry_name} registry")
        registry = registry_class(**init_kwargs)
        self.registry_manager.register_registry(registry)
        registry.load()
    
    def initialize(self):
        """Initialize the application with registries."""
        try:
            self.register_registry(EntityType.API, ApiRegistry)
            self.register_registry(EntityType.DB, DatabaseRegistry)

            self.register_registry(EntityType.INTEGRATION, IntegrationRegistry)
            self.register_registry(EntityType.PROJECT, ProjectRegistry)
            self.register_registry(EntityType.PROJECT_INTEGRATION, ProjectIntegrationRegistry)

            
            self.logger.info("Application initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error initializing application: {e}")
            traceback.print_exc()
            return False

    def configure_logging(self, level=logging.DEBUG):
        """
        Configure global logging with colorized output.
        This should be called once at application startup.
        
        Args:
            level: The default logging level
        """
        # Configure the root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        
        # Remove any existing handlers to avoid duplicates
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Create and configure the colored handler
        handler = colorlog.StreamHandler(stream=sys.stdout)
        formatter = colorlog.ColoredFormatter(
            '%(log_color)s%(asctime)s - %(levelname)s - %(name)s - %(message)s',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
        
        # Set levels for third-party libraries
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)
            
        return root_logger