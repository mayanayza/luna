
from typing import Dict

from src.script.constants import EntityType
from src.script.entity._base import EntityRef
from src.script.entity._projectintegration import ProjectIntegration
from src.script.registry._base import CommandableRegistry


class ProjectIntegrationRegistry(CommandableRegistry):

    def __init__(self):
        super().__init__('project_integration', ProjectIntegration)
        self._pi_project_tree: Dict[Dict[str]] = {}
        self._pi_integration_tree: Dict[Dict[str]] = {}

    def load(self):
        """Load projects from database."""
        self.loader.load_from_database('project_integration')

    def add_pi(self, project_ref: EntityRef, integration_ref: EntityRef) -> ProjectIntegration:
        """Create a new project_integration."""
        try:
            # Create ProjectIntegration
            pi = ProjectIntegration(registry=self, project_id=project_ref.entity_id, integration_id=integration_ref.entity_id, kwargs={})
            self.db.upsert('project_integration', pi)
            self.register_entity(pi)

            # Create registry entries in tree data structures
            project_id = project_ref.entity_id
            integration_id = integration_ref.entity_id

            if project_id not in self._pi_project_tree:
                self._pi_project_tree[project_id] = {}

            if integration_id not in self._pi_integration_tree:
                self._pi_integration_tree[integration_id] = {}

            self._pi_project_tree[project_id][integration_id] = pi.ref
            self._pi_integration_tree[integration_id][project_id] = pi.ref

            return pi
        except Exception as e:
            self.logger.error(f"Error adding integration to project: {e}")
            return None

    def remove_pi(self, project_ref: EntityRef, integration_ref: EntityRef) -> str:
        try:
            # Delete ProjectIntegration
            pi_ref = self.get_pi_by_refs(project_ref, integration_ref)
            pi = self.get_by_ref(pi_ref)
            pi.remove()

            with self.db.transaction():
                table = self.db.dal.project_integration
                self.db.dal(table.id == pi.id).delete()

            # Delete registry entries
            del self._pi_project_tree[project_ref.entity_id][integration_ref.entity_id]
            del self._pi_integration_tree[integration_ref.entity_id][project_ref.entity_id]

            return pi.name
        except Exception as e:
            self.logger.error(f"Error removing integration from project: {e}")
            return None

    def rename_pis_for_project(self, project_ref: EntityRef, **kwargs):
        try:
            pi_refs = self.get_pi_refs_for_project(project_ref)
            for pi_ref in pi_refs:
                pi = self.get_by_ref(pi_ref)
                pi.rename(**kwargs)
            self.db.upsert(EntityType.PROJECT_INTEGRATION, self)
        except Exception as e:
            self.logger.error(f"Error renaming integrations for project: {e}")
            return None

    def remove_pis_for_project(self, project_ref: EntityRef):
        try:
            pi_refs = self.get_pi_refs_for_project(project_ref)
            for pi_ref in pi_refs:
                try:
                    pi = self.get_by_ref(pi_ref)
                    pi.remove()
                    self.logger.debug("Removed integration from project")
                except Exception as e:
                    self.logger.error(f"Error removing integration from project: {e}")

            with self.db.transaction():
                table = getattr(self.db.dal, EntityType.PROJECT_INTEGRATION)
                self.db.dal(table.project_id == project_ref.entity_id).delete()

            if project_ref.entity_id in self._pi_project_tree:
                del self._pi_project_tree[project_ref.entity_id]

        except Exception as e:
            self.logger.error(f"Error removing integrations for project: {e}")
            return None

    def get_pi_refs_for_project(self, project_ref: EntityRef):
        return self._pi_project_tree.get(project_ref.entity_id,{}).values()

    def get_pi_refs_for_integration(self, integration_ref: EntityRef):
        return self._pi_integration_tree.get(integration_ref.entity_id,{}).values()

    def get_pi_by_refs(self, project_ref: EntityRef, integration_ref: EntityRef):
        return self._pi_project_tree.get(project_ref.entity_id,{}).get(integration_ref.entity_id,{})
