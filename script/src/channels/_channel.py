from script.src.config import Config
from script.src.utils import setup_logging


class Channel:
    def __init__(self, channel, config: Config):
        self.config = config
        self.channel = channel
        self.logger = setup_logging(__name__)

    def create(self) -> None:
        """Initialize channel"""
        self.logger.info(f"Creating {self.channel} channel")

    def rename(self, old_name, new_name) -> None:
        """Handle project renames as published on channel"""
        self.logger.info(f"Renaming {old_name} to {new_name} on {self.channel}")

    def stage(self, name) -> None:
        """Stage content for project to be published"""
        self.logger.info(f"Staging content for {self.channel} for {name}")

    def publish(self, name: str) -> None:
        """Publish staged content for project on channel"""
        self.logger.info(f"Publishing to {self.channel} for {name}")