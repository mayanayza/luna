from src.script.config import Config
from src.script.templates.processor import TemplateProcessor
from src.script.utils import setup_logging


class Channel:
    def __init__(self, name, class_name, config: Config) -> None:
        self.config = config
        self.class_name = class_name
        self.tp = TemplateProcessor(config)
        self.logger = setup_logging(name)
        
    def get_commands(self):
        """
        Return a dictionary of supported commands.
        Override in subclasses to provide channel-specific commands.
        """
        return {}
        
    def validate_projects(self, projects):
        """Validate that projects exist. Return the valid projects."""
        from src.script.utils import get_project_path, is_project
        
        valid_projects = []
        for name in projects:
            project_path = get_project_path(self, name)
            if is_project(self, project_path):
                valid_projects.append(name)
            else:
                self.logger.warning(f"Project '{name}' not found or invalid")
        
        return valid_projects
    
    def register_commands(self, registry):
        """Register this channel's commands with the provided registry."""
        commands = self.get_commands()
        if commands:
            registry.register(self.class_name.replace('Handler', '').lower(), commands)