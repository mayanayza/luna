from common.enums import EntityType
from services.base import Service
from .interface import IntegrationInterface


class IntegrationServiceBase(IntegrationInterface, Service):
    """Service for integration operations"""

    def _delete_cleanup(self, integration):
        """Integration-specific delete logic"""
        pi_service = self.registry.manager.get_service_by_entity_type(EntityType.PROJECT_INTEGRATION)
        for pi_uuid, pi in pi_service.get_integration_projects(integration.uuid).items():
            pi_service.delete(pi)

    def add_to_project(self, project, integration):
        pi_service = self.registry.manager.get_service_by_entity_type(EntityType.PROJECT_INTEGRATION)
        return pi_service.create(project_uuid=project.uuid, integration_uuid=integration.uuid)

    # @staticmethod
    # def publish(integration: IntegrationBase, project: Project, **kwargs):
    #     """Publish a project through an integration"""
    #     try:
    #         integration.publish(project, **kwargs)
    #     except Exception as e:
    #         raise RuntimeError(f"Failed to publish project {project.name} via {integration.name}: {e}")
    #
    # @staticmethod
    # def stage(integration: IntegrationBase, project: Project, **kwargs):
    #     """Stage a project through an integration"""
    #     try:
    #         return integration.stage(project, **kwargs)
    #     except Exception as e:
    #         raise RuntimeError(f"Failed to stage project {project.name} via {integration.name}: {e}")