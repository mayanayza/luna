from abc import ABC
from datetime import datetime
from uuid import uuid4

# import pytz
# from typing import TYPE_CHECKING
# from entities.base import Entity
#
# if TYPE_CHECKING:
#     from entities.database import Database
#     from registries.base import Registry


# class NameableEntityMixin:
#     """Adds name property and validation"""
#
#     def __init__(self, registry, **kwargs):
#         super().__init__(registry, **kwargs)
#         self._name = kwargs.get('name', f"entity-{self._uuid}")
#
#     @property
#     def name(self): return self._name
#
#     @name.setter
#     def name(self, value): self._name = value


# class ConfigurableEntityMixin:
#     """Adds configuration storage"""
#
#     def __init__(self, registry, **kwargs):
#         super().__init__(registry, **kwargs)
#         self._config = kwargs.get('config', {})
#
#     @property
#     def config(self): return self._config
# class ListableEntity(Entity, ABC):
#     def __init__(self, registry: 'Registry', **kwargs):
#
#         super().__init__(registry, **kwargs)


# class CreatableEntity(ListableEntity, ABC):
#     def __init__(self, registry: 'Registry', **kwargs):
#
#         super().__init__(registry, **kwargs)
#
#         self._uuid = kwargs.get('uuid', uuid4())
#
#         if not hasattr(self, '_db') or getattr(self, '_db') is None:
#             # Will be set by registry when entity is registered
#             self._db = None
#
#         self._db_id = kwargs.get('db_id', None)
#
#         # Pertains to all stored instances of entity subclasses
#         self.config = kwargs.get('config', {})
#
#         self._fields.update({
#             'date_created': kwargs.get('date_created', datetime.now(pytz.utc).isoformat()),
#         })
#
#     @property
#     def db_id(self):
#         return self._db_id
#
#     @property
#     def db(self) -> 'Database':
#         if not hasattr(self, '_db') or self._db is None:
#             raise RuntimeError(f"Database reference not set for {self.__class__.__name__}")
#         else:
#             return self.registry.manager.get_entity_by_ref(self._db)
#
#     @db.setter
#     def db(self, db_ref):
#         self._db = db_ref
#
#     def db_upsert(self):
#         db_id = self.db.upsert(self.type.value, self)
#         if type(db_id) is int:
#             # Will be returned as int if this is a new record
#             self._db_id = db_id
#

# class NameableEntity(CreatableEntity, ABC):
#     def __init__(self, registry: 'Registry', **kwargs):
#
#         super().__init__(registry, **kwargs)
#
#         self._emoji = kwargs.get('emoji', '')
#
#         self._fields.update({
#             'emoji': self._emoji,
#         })
#
#     @property
#     def emoji(self):
#         return self._emoji
#
#     @emoji.setter
#     def emoji(self, value):
#         self._emoji = value
#
# class CreatableFromModuleEntity(NameableEntity, ABC):
#     def __init__(self, registry, **kwargs):
#         super().__init__(registry, **kwargs)
#
#         self._submodule = kwargs.get('submodule')
#
#         self._fields.update({
#             'submodule': self._submodule,
#         })
#
#     @property
#     def module(self):
#         return self._submodule