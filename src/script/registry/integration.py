from src.script.entity._integration import Integration
from src.script.registry._base import CommandableRegistry


class IntegrationRegistry(CommandableRegistry):
    def __init__(self):
        super().__init__('integration', Integration)

    def load(self):
        """Load integration modules and data."""
        self.load_from_module('src.script.integration')