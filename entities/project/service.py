from typing import Any

from common.enums import EntityType
from entities.project.interface import ProjectInterface
from services.base import Service


class ProjectServiceBase(ProjectInterface, Service):
    """Service for project operations"""

    def _delete_cleanup(self, project):
        """Project-specific deletion cleanup"""
        pi_service = self.registry.manager.get_service_by_entity_type(EntityType.PROJECT_INTEGRATION)
        for pi_uuid, pi in pi_service.get_project_integrations(project.uuid).items():
            pi_service.delete(pi)

    def add_integration(self, project, integration):
        """Project-specific method"""
        pi_service = self.registry.manager.get_service_by_entity_type(EntityType.PROJECT_INTEGRATION)
        return pi_service.create(project_uuid=project.uuid, integration_uuid=integration.uuid)

    def remove_integration(self, project, integration, **kwargs) -> Any:
        pi_service = self.registry.manager.get_service_by_entity_type(EntityType.PROJECT_INTEGRATION)
        return pi_service.delete(project_uuid=project.uuid, integration_uuid=integration.uuid)

    def list_integrations(self, project):
        """Get all integrations for a project"""
        pi_service = self.registry.manager.get_service_by_entity_type(EntityType.PROJECT_INTEGRATION)
        return list(pi_service.get_project_integrations(project.uuid).values())