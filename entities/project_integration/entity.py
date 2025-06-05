from common.enums import EntityType
from registries.base import Registry
from entities.base import Entity
from uuid import UUID

class ProjectIntegrationBase(Entity):
    """ProjectIntegration - bridge between Project and Integration"""

    def __init__(self, registry: Registry, project_uuid: UUID, integration_uuid: UUID, **kwargs):
        super().__init__(registry, **kwargs)

        self._project_uuid = project_uuid
        self._integration_uuid = integration_uuid

        # Get related entities
        integration_registry = registry.manager.get_by_entity_type(EntityType.INTEGRATION)
        project_registry = registry.manager.get_by_entity_type(EntityType.PROJECT)

        integration = integration_registry.get_by_id(integration_uuid)
        project = project_registry.get_by_id(project_uuid)

        # Store UUIDs for database
        self._fields.update({
            'project_uuid': project_uuid,
            'integration_uuid': integration_uuid,
        })

        # Store references
        self._project_ref = project.ref
        self._integration_ref = integration.ref

    def _generate_auto_name(self):
        """Generate name from project and integration"""
        project_registry = self.registry.manager.get_by_entity_type(EntityType.PROJECT)
        integration_registry = self.registry.manager.get_by_entity_type(EntityType.INTEGRATION)

        project = project_registry.get_by_id(self._project_uuid)
        integration = integration_registry.get_by_id(self._integration_uuid)

        return f"{project.name}-{integration.name}"

    @property
    def project_ref(self):
        return self._project_ref
    
    @property
    def integration_ref(self):
        return self._integration_ref
        
    @property
    def project_uuid(self):
        return self._project_uuid
        
    @property
    def integration_uuid(self):
        return self._integration_uuid
    
    @property
    def project(self):
        """Get the associated project"""
        project_registry = self.registry.manager.get_by_entity_type(EntityType.PROJECT)
        return project_registry.get_by_id(self._project_uuid)
    
    @property
    def integration(self):
        """Get the associated integration"""
        integration_registry = self.registry.manager.get_by_entity_type(EntityType.INTEGRATION)
        return integration_registry.get_by_id(self._integration_uuid)