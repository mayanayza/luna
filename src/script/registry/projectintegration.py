
from typing import Dict, List

from src.script.entity._base import EntityRef
from src.script.entity._enum import EntityType
from src.script.entity.projectintegration import ProjectIntegration
from src.script.registry._registry import StorableEntityRegistry


class ProjectIntegrationRegistry(StorableEntityRegistry):

    def __init__(self, manager):
        super().__init__(EntityType.PROJECT_INTEGRATION, ProjectIntegration, manager)
        self._pi_project_tree: Dict[Dict[str]] = {}
        self._pi_integration_tree: Dict[Dict[str]] = {}
        self.database_loader.load(EntityType.PROJECT_INTEGRATION.value)

    
    def add_pi(self, project_ref: EntityRef, integration_ref: EntityRef) -> ProjectIntegration:
        """Create a new project_integration."""
        try:
            # Create ProjectIntegration
            pi = ProjectIntegration(registry=self, project_uuid=project_ref.entity_id, integration_uuid=integration_ref.entity_id, kwargs={})
            self.db.upsert('project_integration', pi)
            self.register_entity(pi)

            # Create registry entries in tree data structures
            project_uuid = project_ref.entity_id
            integration_uuid = integration_ref.entity_id

            if project_uuid not in self._pi_project_tree:
                self._pi_project_tree[project_uuid] = {}

            if integration_uuid not in self._pi_integration_tree:
                self._pi_integration_tree[integration_uuid] = {}

            self._pi_project_tree[project_uuid][integration_uuid] = pi.ref
            self._pi_integration_tree[integration_uuid][project_uuid] = pi.ref

            return pi
        except Exception as e:
            self.logger.error(f"Error adding integration to project: {e}")
            return None

    def remove_pi(self, project_integration) -> str:
        try:
            project_integration.remove()
            project_uuid = project_integration.project_ref.entity_id
            integration_uuid = project_integration.integration_ref.entity_id

            with self.db.transaction():
                table = self.db.dal.project_integration
                self.db.dal(table.id == project_integration.db_id).delete()

            # Delete registry entries
            del self._pi_project_tree[project_uuid][integration_uuid]
            del self._pi_integration_tree[integration_uuid][project_uuid]

            return project_integration.name
        except Exception as e:
            self.logger.error(f"Error removing integration from project: {e}")
            return None

    def rename_pis_for_project(self, project_ref: EntityRef, **kwargs):
        self._rename_pis( self.get_pi_refs_for_project(project_ref), **kwargs )

    def _rename_pis(self, refs, **kwargs):
        try:
            for pi_ref in refs:
                pi = self.get_by_ref(pi_ref)
                pi.rename(**kwargs)
            self.db.upsert(EntityType.PROJECT_INTEGRATION.value, self)
        except Exception as e:
            self.logger.error(f"Error renaming integrations for project: {e}")
            return None
            
    def remove_pis(self, pi_refs: List[EntityRef], removal_for_ref: EntityRef):
        try:
            for pi_ref in pi_refs:
                try:
                    pi = self.get_by_ref(pi_ref)
                    pi.remove()
                    self.logger.debug("Removed integration from project")
                except Exception as e:
                    self.logger.error(f"Error removing integration from project: {e}")

            with self.db.transaction():
                table = getattr(self.db.dal, EntityType.PROJECT_INTEGRATION.value)
                self.db.dal(table.project_uuid == removal_for_ref.entity_id).delete()

            if removal_for_ref.entity_id in self._pi_project_tree:
                del self._pi_project_tree[removal_for_ref.entity_id]

        except Exception as e:
            self.logger.error(f"Error removing integrations for project: {e}")
            return None

    def remove_pis_for_integration(self, integration_ref: EntityRef):
        
        pi_refs = self.get_pi_refs_for_integration(integration_ref)
        self.remove_pis(pi_refs, integration_ref)
        
        if integration_ref.entity_id in self._pi_project_tree:
            del self._pi_integration_tree[integration_ref.entity_id]

    def remove_pis_for_project(self, project_ref: EntityRef):
        
        pi_refs = self.get_pi_refs_for_project(project_ref)
        self.remove_pis(pi_refs, project_ref)
        
        if project_ref.entity_id in self._pi_project_tree:
            del self._pi_project_tree[project_ref.entity_id]

    def get_pi_refs_for_project(self, project_ref: EntityRef):
        return self._pi_project_tree.get(project_ref.entity_id,{}).values()

    def get_pi_refs_for_integration(self, integration_ref: EntityRef):
        return self._pi_integration_tree.get(integration_ref.entity_id, {}).values()

    def get_pi_by_refs(self, project_ref: EntityRef, integration_ref: EntityRef):
        return self._pi_project_tree.get(project_ref.entity_id,{}).get(integration_ref.entity_id,None)
