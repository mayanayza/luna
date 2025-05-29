import logging
from typing import (
    Dict,
    List,
    Optional,
)

from src.script.common.constants import EntityType
from src.script.entity._base import Entity, EntityRef
from src.script.registry._base import Registry
from src.script.registry._registry import StorableEntityRegistry


class RegistryManager:
    """Central manager for all registries."""
    def __init__(self):
        self._registries: Dict[str, 'Registry'] = {}
        self._registries_by_entity_type: Dict[EntityType, 'Registry'] = {}
        self._db_ref = None
        # self._command_dispatcher = None
        self.logger = logging.getLogger(__name__)
        self._next_id: int = 1

    @property
    def db_ref(self):
        return self._db_ref
    

    def update_db(self, db_ref: EntityRef):
        self._db_ref = db_ref

        for registry in self._registries.values():

            if isinstance(registry, StorableEntityRegistry):
                registry.db = self._db_ref
    
    def register_registry(self, registry):
        """Register a registry with the manager."""
        self._registries[registry.uuid] = registry
        registry.manager = self

        # Add to name index if the entity has an entity_type attribute
        if hasattr(registry, 'entity_type'):
            self._registries_by_entity_type[registry.entity_type] = registry
        
    def get_by_id(self, registry_id: str) -> Optional['Registry']:
        return self._registries.get(registry_id)

    def get_by_entity_type(self, entity_type: EntityType) -> Optional['Registry']:
        return self._registries_by_entity_type.get(entity_type)
    
    def get_entity(self, ref: EntityRef) -> Optional['Entity']:
        registry = self.get_by_id(ref.registry_id)
        if registry:
            return registry.get_by_id(ref.entity_id)
        return None

    def get_all_registries(self) -> List['Registry']:
        return self._registries.values()

    def get_entity_by_ref(self, ref: EntityRef) -> Optional['Entity']:
        return self.get_entity(ref)

    def find_entities_by_filter(self, filter_func, registry_id: Optional[str] = None) -> List[EntityRef]:
        """
        Find entities across registries using a filter function.
        
        Args:
            filter_func: Function that takes an entity and returns True/False
            registry_id: Optional registry to limit the search to
            
        Returns:
            List of EntityRefs for matching entities
        """
        results = []
        
        if registry_id:
            registry = self.get_by_id(registry_id)
            if registry:
                for entity in registry.get_all_entities():
                    if filter_func(entity):
                        results.append(EntityRef(entity.uuid, registry.uuid))
        else:
            for reg_id, registry in self._registries.items():
                for entity in registry.get_all_entities():
                    if filter_func(entity):
                        results.append(EntityRef(entity.uuid, reg_id))
        
        return results