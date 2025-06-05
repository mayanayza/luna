from api.cli.base import SubparserBase
from entities.integration.interface import IntegrationInterface


class IntegrationSubparserBase(SubparserBase, IntegrationInterface):
    """Project entity subparser with integration management capabilities"""

    def __init__(self, ctx):
        super().__init__(ctx)
