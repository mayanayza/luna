import logging
import sys
import traceback

import colorlog
from src.script.registry._manager import RegistryManager
from src.script.registry.api import ApiRegistry
from src.script.registry.db import DatabaseRegistry
from src.script.registry.handler import HandlerRegistry
from src.script.registry.integration import IntegrationRegistry
from src.script.registry.project import ProjectRegistry
from src.script.registry.projectintegration import ProjectIntegrationRegistry


class ExceptionFormatter(colorlog.ColoredFormatter):
    def format(self, record):
        # Auto-include exception info for ERROR and CRITICAL if there's an active exception
        if record.levelno >= logging.ERROR and not record.exc_info and sys.exc_info()[0] is not None:
            record.exc_info = sys.exc_info()
        return super().format(record)

class ApplicationContext:
    """Central coordination point for application setup"""
    
    def __init__(self):

        self.configure_logging()

        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self.registry_manager = RegistryManager()
            
    def get_registry(self, entity_type):
        return self.registry_manager.get_by_entity_type(entity_type)
    
    def initialize(self):
        """Initialize the application with registries."""
        try:
            HandlerRegistry(self.registry_manager)
            DatabaseRegistry(self.registry_manager)

            IntegrationRegistry(self.registry_manager)
            ProjectRegistry(self.registry_manager)
            ProjectIntegrationRegistry(self.registry_manager)

            ApiRegistry(self.registry_manager)
            
            self.logger.info("Application initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error initializing application: {e}")
            traceback.print_exc()
            return False

    def configure_logging(self, level=logging.DEBUG):
        """
        Configure global logging with colorized output including custom SUCCESS level.
        This should be called once at application startup.
        
        Args:
            level: The default logging level
        """
        # Define custom SUCCESS log level
        SUCCESS_LEVEL = 25
        logging.addLevelName(SUCCESS_LEVEL, 'SUCCESS')

        def success(self, message, *args, **kwargs):
            """
            Log a message with severity 'SUCCESS'.
            """
            if self.isEnabledFor(SUCCESS_LEVEL):
                self._log(SUCCESS_LEVEL, message, args, **kwargs)

        # Add success method to Logger class
        logging.Logger.success = success
        
        # Configure the root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        
        # Remove any existing handlers to avoid duplicates
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Create and configure the colored handler
        handler = colorlog.StreamHandler(stream=sys.stdout)
        formatter = ExceptionFormatter(
            '%(log_color)s%(asctime)s - %(levelname)s - %(name)s - %(message)s',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'blue',
                'SUCCESS': 'green',
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