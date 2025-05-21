from src.script.entity._project import Project
from src.script.registry._command import CommandableRegistry


class ProjectRegistry(CommandableRegistry):
    def __init__(self):
        super().__init__('project', Project)

    def load(self):
        """Load projects from database."""
        self.load_from_database('project')

    def handle_create(self, name: str, title: str = "", emoji: str = ""):
        """Create a new project."""
        project = Project(self)
        project = project.create(name=name, title=title, emoji=emoji)
        self.db.upsert('project', project)
        self.register_entity(project)
        return project