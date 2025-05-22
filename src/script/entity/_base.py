import logging
import uuid
from abc import ABC
from datetime import datetime
from typing import (
    Any,
    Dict,
)

from src.script.registry._base import Registry


class EntityRef:
    """A reference to an entity that doesn't rely on mutable attributes like name."""
    def __init__(self, entity_id: uuid.UUID, registry_id: str):
        self.entity_id = entity_id
        self.registry_id = registry_id
    
    def __eq__(self, other):
        if not isinstance(other, EntityRef):
            return False
        return self.entity_id == other.entity_id and self.registry_id == other.registry_id
    
    def __hash__(self):
        return hash((self.entity_id, self.registry_id))
    
    def __str__(self):
        return f"{self.registry_id}:{self.entity_id}"

class EntityBase(ABC):
    """Base class for all entities in the system."""
    
    def __init__(self, registry: 'Registry'):

        if not self._name:
            raise ValueError(f"No name provided to Entity {__name__} upon init. Aborting.")
            return

        self._registry = registry
        self._logger = logging.getLogger(f"{self.__class__.__name__}")
        
    def __str__(self):
        return f"<{self.__class__.__name__} object, name '{self._name}', id '{self._id}'>"

    @property
    def registry(self):
        return self._registry
    
    @property
    def logger(self):
        return self._logger
    
    @property
    def ref(self) -> EntityRef:
        """Get a reference to this entity."""
        return EntityRef(self.id, self.registry.id)

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, val):
        self._id = val

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, val):
        self._name = val
    
class ModuleEntity(EntityBase):
    def __init__(self, registry: 'Registry', name: str):
        self._id = registry.get_next_id()
        self._name = name

        super().__init__(registry)

class StorableEntity(EntityBase):
    def __init__(self, registry: 'Registry', **kwargs):
        
        id_ = kwargs.get('id', None)
        name = kwargs.get('name', None)
        data = kwargs.get('data', {})
        date_created = kwargs.get('date_created', datetime.now().strftime('%d-%b-%Y-%H:%M:%S'))

        self._id = id_ if id_ else registry.get_next_id()
        self._name = name
        self._data: Dict[str, Any] = data
        self._date_created = date_created

        self._db = None
        self._db_additional_fields = {}

        super().__init__(registry)

    @property
    def db_additional_fields(self):
        return self._db_additional_fields

    @property
    def data(self) -> Dict[str, Any]:
        """Get a copy of the entity's data."""
        return self._data.copy()
    
    @data.setter
    def data(self, val: Dict[str, Any]):
        """Set the entity's data."""
        self._data = val
    
    def get_data(self, key: str) -> Any:
        """Get a specific data item by key."""
        return self._data.get(key)
    
    def set_data(self, key: str, value: Any) -> None:
        """Set a specific data item."""
        self._data[key] = value

    @property
    def date_created(self):
        return self._date_created

    @date_created.setter
    def date_created(self, val):
        self._date_created = val
    
    @property
    def db(self):
        if not hasattr(self, '_db') or self._db is None:
            raise RuntimeError(f"Database reference not set for {self.__class__.__name__}")
        else:
            return self._db

    @db.setter
    def db(self, val):
        self._db = val