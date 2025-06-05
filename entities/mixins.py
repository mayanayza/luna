from abc import ABC
from datetime import datetime

import pytz
from typing import TYPE_CHECKING

from entities.base import Entity

if TYPE_CHECKING:
    from entities.database import Database


class EntityMixin(Entity, ABC):
    pass

class UserNameablePropertyMixin(EntityMixin, ABC):
    """Provides editable name property for entities"""

    def __init__(self, registry, **kwargs):
        super().__init__(registry, **kwargs)
        provided_name = kwargs.get('name')
        if provided_name:
            self._name = provided_name
        else:
            self._name = self._generate_default_name()

    def __str__(self):
        return f"{self.__class__.__name__}, name '{self._name}', id '{self._uuid}'"

    def _generate_default_name(self):
        return f"{self.__class__.__name__.lower()}-{str(self._uuid)[:8]}"

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value


class ReadOnlyNamePropertyMixin(EntityMixin, ABC):
    """Provides read-only name property for entities"""

    def __init__(self, registry, **kwargs):
        super().__init__(registry, **kwargs)
        self._name = self._generate_auto_name(**kwargs)

    def __str__(self):
        return f"{self.__class__.__name__}, name '{self._name}', id '{self._uuid}'"

    def _generate_auto_name(self, **kwargs):
        return f"{self.__class__.__name__.lower()}-{str(self._uuid)[:8]}"

    @property
    def name(self): return self._name


class DatabasePropertyMixin(EntityMixin, ABC):
    """Provides database persistence properties for entities"""

    def __init__(self, registry, **kwargs):
        super().__init__(registry, **kwargs)

        if not hasattr(self, '_db') or getattr(self, '_db') is None:
            # Will be set by registry when entity is registered
            self._db = None

        self._db_id = kwargs.get('db_id', None)
        self._fields.update({
            'date_created': kwargs.get('date_created', datetime.now(pytz.utc).isoformat())
        })

    @property
    def db_id(self): return self._db_id

    @property
    def db(self) -> 'Database':
        if not hasattr(self, '_db') or self._db is None:
            raise RuntimeError(f"Database reference not set for {self.__class__.__name__}")
        else:
            return self.registry.manager.get_entity_by_ref(self._db)

    @db.setter
    def db(self, db_ref):
        self._db = db_ref

    def db_upsert(self):
        db_id = self.db.upsert(self.type.value, self)
        if isinstance(db_id, int):
            self._db_id = db_id


class ConfigPropertyMixin(EntityMixin, ABC):
    """Provides configuration storage for entities"""

    def __init__(self, registry, **kwargs):
        super().__init__(registry, **kwargs)
        self._config = kwargs.get('config', {})

    @property
    def config(self): return self._config


# class EmojiPropertyMixin(EntityMixin, ABC):
#     """Provides emoji property for entities"""
#
#     def __init__(self, registry, **kwargs):
#         super().__init__(registry, **kwargs)
#         self._emoji = kwargs.get('emoji', '')
#         self._fields.update({'emoji': self._emoji})
#
#     @property
#     def emoji(self): return self._emoji
#
#     @emoji.setter
#     def emoji(self, value):
#         self._emoji = value
#         self._fields['emoji'] = value

class ImplementationPropertyMixin(EntityMixin, ABC):
    """Provides module information for entities"""

    def __init__(self, registry, **kwargs):
        super().__init__(registry, **kwargs)
        self._submodule = kwargs.get('submodule')
        if self._submodule:
            self._fields.update({'submodule': self._submodule})
