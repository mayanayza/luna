from typing import Dict

from common.enums import EntityType
from uuid import UUID

from entities.project_integration.entity import ProjectIntegrationBase
from entities.project_integration.interface import ProjectIntegrationInterface
from services.base import Service


class ProjectIntegrationServiceBase(ProjectIntegrationInterface, Service):
    """Service for managing project-integration relationships"""

    def _create_cleanup(self, project_integration:ProjectIntegrationBase):
        """Create a new project integration"""
        project = project_integration.project
        integration = project_integration.integration
        # Check if relationship already exists
        existing = self.registry.get_pi_by_ids(project.uuid, integration.uuid)
        if existing:
            raise ValueError(f"Integration '{integration.name}' already added to project '{project.name}'")

        # Set up the integration
        try:
            integration.setup(project)
        except Exception as e:
            raise RuntimeError(f"Failed to setup integration {integration.name} for project {project.name}: {e}")

    def stage(self, project_integration:ProjectIntegrationBase, **kwargs):
        self.logger.info(f"Staging {project_integration}")
        try:
            integration = project_integration.integration
            project = project_integration.project
            integration.stage(project, **kwargs)
        except Exception as e:
            raise RuntimeError(f"Failed to stage {project_integration.name}: {e}")

    def publish(self, project_integration:ProjectIntegrationBase, **kwargs):
        self.logger.info(f"Publishing {project_integration}")
        try:
            integration = project_integration.integration
            project = project_integration.project
            integration.publish(project, **kwargs)
        except Exception as e:
            raise RuntimeError(f"Failed to publish {project_integration.name}: {e}")

    def get_project_integrations(self, project_uuid: str) -> Dict[UUID, ProjectIntegrationBase]:
        """Get all implementations used by project"""
        return self.registry.get_by_project_uuid(project_uuid)

    def get_integration_projects(self, integration_uuid: str) -> Dict[UUID, ProjectIntegrationBase]:
        """Get all projects using an integration"""
        return self.registry.get_by_integration_uuid(integration_uuid)

    def rename_integrations_for_project(self, project_uuid: str, old_name: str) -> None:
        """Handle project rename for all implementations"""
        project_integrations = self.get_project_integrations(project_uuid).values()

        project_registry = self.registry.manager.get_by_entity_type(EntityType.PROJECT)
        project = project_registry.get_by_id(project_uuid)

        integration_registry = self.registry.manager.get_by_entity_type(EntityType.INTEGRATION)
        
        for integration_uuid, pi in project_integrations:
            try:
                integration = integration_registry.get_by_id(integration_uuid)
                integration.rename(project, old_name=old_name)
            except Exception as e:
                self.logger.error(f"Failed to rename integration {pi.name}: {e}")

    def remove_integrations_for_project(self, project_uuid: str) -> None:
        project_integrations = self.get_project_integrations(project_uuid).values()

        project_registry = self.registry.manager.get_by_entity_type(EntityType.PROJECT)
        project = project_registry.get_by_id(project_uuid)

        integration_registry = self.registry.manager.get_by_entity_type(EntityType.INTEGRATION)

        for integration_uuid, pi in project_integrations:
            try:
                integration = integration_registry.get_by_id(integration_uuid)
                integration.remove(project)
            except Exception as e:
                self.logger.error(f"Failed to rename integration {pi.name}: {e}")

    def remove_projects_for_integration(self, integration_uuid: str) -> None:
        integration_projects = self.get_integration_projects(integration_uuid).values()

        # noinspection DuplicatedCode
        integration_registry = self.registry.manager.get_by_entity_type(EntityType.INTEGRATION)
        integration = integration_registry.get_by_id(integration_uuid)

        project_registry = self.registry.manager.get_by_entity_type(EntityType.PROJECT)

        for project_uuid, pi in integration_projects:
            try:
                project = project_registry.get_by_id(project_uuid)
                integration.remove(project)
            except Exception as e:
                self.logger.error(f"Failed to rename integration {pi.name}: {e}")
