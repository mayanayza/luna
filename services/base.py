import logging
from abc import ABC

from common.enums import EntityType, ApplicationLayer
from entities.base import Entity

class Service(ABC):
    """Base service class with enhanced error logging"""

    layer = ApplicationLayer.SERVICE

    # Provided by EntityMixin
    entity_type: EntityType = NotImplemented
    entity_type_name: str = NotImplemented

    # Set at init using import
    entity_class: Entity = NotImplemented
    
    def __init__(self, registry):
        self.registry = registry
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self.logger.debug(f"Initialized {self.__class__.__name__}")