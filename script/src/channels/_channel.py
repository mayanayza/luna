from script.src.config import Config
from script.src.templates.processor import TemplateProcessor
from script.src.utils import setup_logging


class Channel:
    def __init__(self, name, class_name, config: Config) -> None:
        self.config = config
        self.class_name = class_name
        self.tp = TemplateProcessor(config)
        self.logger = setup_logging(name)

    def create(self, name: str) -> None:
        """Initialize channel"""
        self.logger.error(f"No create function exists for {self.class_name}")

    def rename(self, old_name: str, new_name: str) -> None:
        """Handle project renames as published on channel"""
        self.logger.error(f"No rename function exists for {self.class_name}")

    def stage(self, name: str) -> None:
        """Stage content for project to be published"""
        self.logger.error(f"No stage function exists for {self.class_name}")

    def publish(self, name: str) -> None:
        """Publish staged content for project on channel"""
        self.logger.error(f"No publish function exists for {self.class_name}")

    def delete(self, name: str) -> None:
        """Delete channel for project"""
        self.logger.error(f"No delete function exists for {self.class_name}")