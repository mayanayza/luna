from src.script.entity._enum import EntityType
from src.script.entity.project import Project
from src.script.registry._registry import CreatableEntityRegistry


class ProjectRegistry(CreatableEntityRegistry):

    def __init__(self, manager):
        super().__init__(EntityType.PROJECT, Project, manager)

        self.database_loader.load(EntityType.PROJECT.value)

    @classmethod
    def handle_create(cls, registry, name: str, title: str = "", emoji: str = "", **kwargs):
        """Create a new project."""
        project = Project(registry=registry, name=name, title=title, emoji=emoji, kwargs={})
        registry.db.upsert(EntityType.PROJECT.value, project)
        return project