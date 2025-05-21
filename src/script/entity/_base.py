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



class StorableEntity:
    def __init__(self, registry: 'Registry'):
        self._db = None
        super().__init__(registry)

    @property
    def db_additional_fields(self):
        return {}
    
    @property
    def db(self):
        if not hasattr(self, '_db') or self._db is None:
            raise RuntimeError(f"Database reference not set for {self.__class__.__name__}")
        else:
            return self._db

    @db.setter
    def db(self, val):
        self._db = val

class EntityBase(ABC):
    """Base class for all entities in the system."""
    
    def __init__(self, registry: 'Registry'):
        self.registry = registry
        self._id = registry.get_next_id()
        self._data: Dict[str, Any] = {}
        self._date_created = datetime.now().strftime('%d-%b-%Y-%H:%M:%S')
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self.registry.register_entity(self)
        
    @property
    def ref(self) -> EntityRef:
        """Get a reference to this entity."""
        return EntityRef(self.id, self.registry.registry_id)

    @property
    def id(self):
        return self._id

    @property
    def date_created(self):
        return self._date_created

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, val):
        self._name = val
    
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

    def load(self, id, name, date_created, data, **kwargs):
        """Set properties when loading entity data from database"""
        self._id = id
        self._name = name
        self._date_created = date_created
        self._data = data
        self.registry.register_entity(self)


