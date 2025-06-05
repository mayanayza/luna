import logging
from abc import ABC
from typing import TYPE_CHECKING, Type
from uuid import UUID, uuid4

from common.enums import EntityType, ApplicationLayer

if TYPE_CHECKING:
    pass


class EntityRef:

    layer = ApplicationLayer.ENTITY
    """A reference to an entity that doesn't rely on mutable attributes like name."""
    def __init__(self, entity_id: UUID, registry_id: UUID):
        self.entity_id = entity_id
        self.registry_id = registry_id
    
    def __eq__(self, other):
        if not isinstance(other, EntityRef):
            return False
        return self.entity_id == other.entity_id and self.registry_id == other.registry_id
    
    def __hash__(self):
        return hash((self.entity_id, self.registry_id))
    
    def __str__(self):
        return f"EntityRef {self.registry_id}:{self.entity_id}"


class Entity(ABC):
    """Only universal properties"""

    layer = ApplicationLayer.ENTITY

    def __init__(self, registry, **kwargs):
        self._uuid = kwargs.get('uuid', uuid4())
        self._registry = registry
        self._fields = {}

        self.logger = logging.getLogger(f"{self.__class__.__name__}")

    def __str__(self):
        return self.__class__.__name__

    def __init_subclass__(cls, **kwargs):
        """
        Automatically wrap subclass __init__ methods to call self.register_entity(self)
        when the deepest subclass completes initialization.
        """
        super().__init_subclass__(**kwargs)

        # Store the original __init__ method
        original_init = cls.__init__

        def wrapped_init(self, *args, **kwargs):
            # Track initialization depth
            if not hasattr(self, '_init_depth'):
                self._init_depth = 0
            self._init_depth += 1

            try:
                # Call the original __init__
                original_init(self, *args, **kwargs)
            finally:
                # Decrease depth after initialization
                self._init_depth -= 1

                # If we're back to depth 0, all initialization is complete
                if self._init_depth == 0:
                    self.registry.register_entity(self)

        # Replace the class's __init__ with our wrapped version
        cls.__init__ = wrapped_init

    @property
    def uuid(self): return self._uuid

    @property
    def registry(self): return self._registry

    @property
    def fields(self): return self._fields

    def set_field(self, field, value):
        self._fields[field] = value

    def get_field(self, field):
        return self._fields[field]

    @property
    def ref(self) -> EntityRef:
        """Get a reference to this entity."""
        return EntityRef(self.uuid, self.registry.uuid)

# class Entity(ABC):
#     """Base class for all entities in the system."""
#
#     type: Type[EntityType]
#
#     def __init__(self, registry: 'Registry', **kwargs):
#
#         name = kwargs.get('name', None)
#         filename = kwargs.get('filename', None)
#
#         self._uuid: UUID = uuid4()
#         self._name: str = (
#             name if name else
#             filename if filename else
#             f"{Entity.type.value}-{self._uuid}"
#         )
#
#         self._registry = registry
#         self._logger = logging.getLogger(f"{self.__class__.__name__}")
#
#         # Pertains to all entity subclasses
#         self._fields = {}
#
#
#
