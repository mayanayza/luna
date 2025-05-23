from src.script.constants import EntityType
from src.script.entity._project import Project
from src.script.registry._base import CommandableRegistry


class ProjectRegistry(CommandableRegistry):
    def __init__(self):
        super().__init__(EntityType.PROJECT, Project)

    def load(self):
        """Load projects from database."""
        self.loader.load_from_database(EntityType.PROJECT)

    def handle_create(self, name: str, title: str = "", emoji: str = "", **kwargs):
        """Create a new project."""
        project = Project(registry=self, name=name, title=title, emoji=emoji, kwargs={})
        self.db.upsert(EntityType.PROJECT, project)
        self.register_entity(project)
        return project