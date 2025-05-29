from src.script.common.constants import EntityType
from src.script.entity.project import Project
from src.script.registry._registry import CreatableEntityRegistry


class ProjectRegistry(CreatableEntityRegistry):

    def __init__(self, manager):
        super().__init__(EntityType.PROJECT, Project, manager)

        self.loader.load_from_database(EntityType.PROJECT.value)

    @classmethod
    def handle_create(cls, registry, name: str, title: str = "", emoji: str = "", **kwargs):
        """Create a new project."""
        project = Project(registry=registry, name=name, title=title, emoji=emoji, kwargs={})
        registry.db.upsert(EntityType.PROJECT.value, project)
        return project