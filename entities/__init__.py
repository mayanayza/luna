from abc import ABC
from typing import Dict, Any, Type

from api.cli.base import SubparserBase
from common.capabilities import EntityCapabilities
from common.enums import ApplicationLayer, EntityType
from registries.base import Registry
from services.base import Service
from .base import Entity

class EntityInitializer(ABC):
    """Initializes registry, service, entity, and CLI classes with corresponding mixins from capabilities"""

    def __init__(self,
                 entity_type: EntityType,
                 capabilities: Type[EntityCapabilities],
                 entity_class_base: Type[Entity],
                 service_class_base: Type[Service],
                 registry_class_base: Type[Registry],
                 cli_class_base: Type[SubparserBase]):
        self.capabilities = capabilities
        self.entity_type = entity_type
        self.class_prefix = entity_type.value.title()

        self.class_bases = {
            ApplicationLayer.ENTITY: entity_class_base,
            ApplicationLayer.REGISTRY: registry_class_base,
            ApplicationLayer.CLI: cli_class_base,
            ApplicationLayer.SERVICE: service_class_base,
        }

    def create_classes(self):

        layer_classes: Dict[ApplicationLayer, Any] = {}
        self.capabilities.entity_type = self.entity_type

        for layer in ApplicationLayer:
            layer_class_base = self.class_bases[layer]
            layer_class_name = f'{self.class_prefix.title()}{layer.value.title()}'
            layer_class = self.capabilities.create_composed_class(layer_class_name, layer_class_base)
            layer_classes[layer] = layer_class

        return self._set_class_attributes(layer_classes)

    def _set_class_attributes(self, layer_classes: Dict[ApplicationLayer, Any]):
        service_class = layer_classes[ApplicationLayer.SERVICE]
        entity_class = layer_classes[ApplicationLayer.ENTITY]
        registry_class = layer_classes[ApplicationLayer.REGISTRY]

        registry_class.entity_class = entity_class
        registry_class.service_class = service_class

        service_class.entity_class = entity_class

        entity_class.type = self.entity_type

        for layer_class in layer_classes.values():
            layer_class.entity_type = self.entity_type

        return layer_classes

    def validate_capabilities(self):
        errors = self.capabilities.validate_capabilities()
        if errors:
            raise TypeError(f"{self.entity_type.value.title()} validation failed: {errors}")