from abc import ABC, abstractmethod

from src.script.common.enums import EntityType
from src.script.common.mixins.interfaces import CreatableFromModuleMixin, NameableMixin, CreatableMixin, ListableMixin
from src.script.entities.database import Database
from src.script.entities.integration import Integration
from src.script.entities.project import Project
from src.script.entities.project_integration import ProjectIntegration

class EntityMixin(ABC):

    is_entity_mixin = True # used for base classes which need to enforce EntityMixin, check this instead of subclass membership to avoid circular import

    @property
    @classmethod
    @abstractmethod
    def entity_type(cls) -> EntityType:
        pass

    @property
    @classmethod
    @abstractmethod
    def entity_class(cls) -> EntityType:
        pass

    @property
    def entity_type_name(self):
        return self.entity_type.value

class ProjectMixin(EntityMixin, NameableMixin):
    entity_type = EntityType.PROJECT
    entity_class = Project

class IntegrationMixin(EntityMixin, CreatableFromModuleMixin):
    entity_type = EntityType.INTEGRATION
    entity_class = Integration
    package = 'src.script.entities.integrations'

class ProjectIntegrationMixin(EntityMixin, CreatableMixin):
    entity_type = EntityType.PROJECT_INTEGRATION
    entity_class = ProjectIntegration

class DatabaseMixin(EntityMixin, ListableMixin):
    entity_type = EntityType.DATABASE
    entity_class = Database
