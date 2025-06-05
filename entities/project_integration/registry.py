
from typing import Dict
from uuid import UUID
from entities.project_integration.entity import ProjectIntegrationBase
from registries.base import Registry


class ProjectIntegrationRegistryBase(Registry):

    def __init__(self, manager):
        super().__init__(manager)
        self._pi_by_project: Dict[UUID, Dict[UUID, ProjectIntegrationBase]] = {}
        self._pi_by_integration: Dict[UUID, Dict[UUID, ProjectIntegrationBase]] = {}

    def register_entity(self, project_integration: ProjectIntegrationBase):

        project_uuid = project_integration.project_uuid
        integration_uuid = project_integration.integration_uuid

        if project_uuid not in self._pi_by_project:
            self._pi_by_project[project_uuid] = {}

        if integration_uuid not in self._pi_by_integration:
            self._pi_by_integration[integration_uuid] = {}

        self._pi_by_project[project_uuid][integration_uuid] = project_integration
        self._pi_by_integration[integration_uuid][project_uuid] = project_integration

        super().register_entity(project_integration)

    def unregister_entity(self, project_integration: ProjectIntegrationBase) -> None:

        project_uuid = project_integration.project_uuid
        integration_uuid = project_integration.integration_uuid

        del self._pi_by_project[project_uuid][integration_uuid]
        del self._pi_by_integration[integration_uuid][project_uuid]

        super().unregister_entity(project_integration)

    def get_by_project_uuid(self, project_uuid) -> Dict[UUID, ProjectIntegrationBase]:
        return self._pi_by_project[project_uuid]

    def get_by_integration_uuid(self, integration_uuid) -> Dict[UUID, ProjectIntegrationBase]:
        return self._pi_by_integration[integration_uuid]

    def get_pi_by_ids(self, project_uuid: UUID, integration_uuid: UUID):
        return self._pi_by_project.get(project_uuid,{}).get(integration_uuid, None)
