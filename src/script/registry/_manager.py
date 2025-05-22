import logging
from typing import (
    Dict,
    List,
    Optional,
)

from src.script.entity._base import EntityBase, EntityRef, StorableEntity
from src.script.registry._base import Registry


class RegistryManager:
    """Central manager for all registries."""
    def __init__(self):
        self._registries: Dict[str, 'Registry'] = {}
        self._registries_by_name: Dict[str, 'Registry'] = {}
        self._db_ref = None
        # self._command_dispatcher = None
        self.logger = logging.getLogger(__name__)
        self._next_id: int = 1

    # def set_command_dispatcher(self, dispatcher):
    #     """Set the command dispatcher for this manager and all commandable registries."""
    #     self._command_dispatcher = dispatcher
        
    #     # Update all existing commandable registries
    #     for registry in self._registries.values():
    #         if hasattr(registry, 'command_dispatcher'):
    #             registry.command_dispatcher = dispatcher

    def update_db(self, db_ref: EntityRef):
        self._db_ref = db_ref

        for registry in self._registries.values():
            if issubclass(registry.entity_class, StorableEntity):
                registry.db = self.get_db()
    
    def get_db(self):
        return self.get_entity(self._db_ref)

    def get_next_id(self) -> int:
        """Get the next available entity ID."""
        next_id = self._next_id
        self._next_id += 1
        return next_id

    def register_registry(self, registry):
        """Register a registry with the manager."""
        registry.id = self.get_next_id()
        self._registries[registry.id] = registry
        registry.manager = self

        # Add to name index if the entity has a name attribute
        if hasattr(registry, 'name'):
            self._registries_by_name[registry.name] = registry
        
        # # Auto-set command dispatcher if available
        # if self._command_dispatcher and hasattr(registry, 'command_dispatcher'):
        #     registry.command_dispatcher = self._command_dispatcher

        if issubclass(registry.entity_class, StorableEntity):
            registry.db = self.get_entity(self._db_ref)

        # Auto-load APIs if apis exists
        # if hasattr(registry, 'load_apis') and 'apis' in self._registries:
        #     registry.load_apis(self._registries['apis'])
        
    def get_by_id(self, registry_id: str) -> Optional['Registry']:
        return self._registries.get(registry_id)

    def get_by_name(self, registry_name: str) -> Optional['Registry']:
        return self._registries_by_name.get(registry_name)
    
    def get_entity(self, ref: EntityRef) -> Optional['EntityBase']:
        registry = self.get_by_id(ref.registry_id)
        if registry:
            return registry.get_by_id(ref.entity_id)
        return None

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
                        results.append(EntityRef(entity.id, registry.registry_id))
        else:
            for reg_id, registry in self._registries.items():
                for entity in registry.get_all_entities():
                    if filter_func(entity):
                        results.append(EntityRef(entity.id, reg_id))
        
        return results