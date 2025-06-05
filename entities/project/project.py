from typing import Any, List

from common.enums import EntityType
from entities.integration.entity import IntegrationBase
from entities.project import Project
from services.base import Service


class ProjectServiceBase(Service):
    """Service for project operations"""
    
    def __init__(self, project_registry):
        super().__init__(project_registry)
        self.integration_registry = project_registry.manager.get_by_entity_type(EntityType.INTEGRATION)

    def _rename(self, project, old_name, old_emoji) -> None:
        """Project-specific rename logic"""
        pi_registry = self.registry.manager.get_by_entity_type(EntityType.PROJECT_INTEGRATION)
        pi_service = pi_registry.service

        pi_service.rename_integrations_for_project(
            project_uuid=project.uuid,
            new_name=project.name,
            new_emoji=project.emoji,
            old_name=old_name,
            old_emoji=old_emoji
        )

    def _delete(self, project: Project) -> None:
        """Project-specific delete logic"""
        pi_registry = self.registry.manager.get_by_entity_type(EntityType.PROJECT_INTEGRATION)
        pi_registry.remove_pis_for_project(project.ref)
    
    def add_integration(self, project: Project, integration: IntegrationBase) -> Any:
        """Add an integration to a project"""
        try:
            pi_registry = self.registry.manager.get_by_entity_type(EntityType.PROJECT_INTEGRATION)
            pi_service = pi_registry.service

            pi = pi_service.create(project=project, integration=integration)
            pi.setup()
            
            self.logger.info(f"Added integration '{pi.name}' to project {project.name}")
            return pi
            
        except Exception as e:
            raise RuntimeError(f"Failed to add integration to {project.name}: {e}")

    def get_integrations(self, project: Project) -> List:
        """Get all implementations for a project"""
        pi_registry = self.registry.manager.get_by_entity_type(EntityType.PROJECT_INTEGRATION)
        return pi_registry.get_by_project_uuid(project.uuid).values()

