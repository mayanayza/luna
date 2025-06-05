import click

from api.cli.base import SubparserBase
from common.enums import EntityType, CommandType
from .service import ProjectServiceBase
from entities.project.interface import ProjectInterface


class ProjectSubparserBase(SubparserBase, ProjectInterface):
    """Project entity subparser with integration management capabilities"""

    def __init__(self, ctx):
        super().__init__(ctx)
        self.service: ProjectServiceBase

    @click.command(CommandType.ADD_INTEGRATION.value)
    @click.argument('project_name')
    @click.argument('integration_name')
    def add_integration(self, project_name: str, integration_name: str):
        """Add an integration to a project"""
        self.logger.info(f"Adding integration '{integration_name}' to project '{project_name}'")

        try:
            project = self._validate_entity_name_of_type(project_name, EntityType.PROJECT)
            integration = self._validate_entity_name_of_type(integration_name, EntityType.INTEGRATION)

            self.logger.debug(f"Adding integration {integration.name} to project {project.name}")
            self.service.add_integration(project, integration)

            click.echo(f"✓ Added integration '{integration.name}' to project '{project.name}'")
            self.logger.info("Successfully added integration to project")

        except ValueError as e:
            self.logger.error(f"Validation error: {e}")
            click.echo(f"Error: {e}", err=True)
            raise click.ClickException(str(e))
        except Exception as e:
            self.logger.error(f"Error adding integration: {e}", exc_info=True)
            click.echo(f"Error: {e}", err=True)
            raise click.ClickException("Failed to add integration")

    @click.command(CommandType.REMOVE_INTEGRATION.value)
    @click.argument('project_name')
    @click.argument('integration_name')
    def remove_integration(self, project_name: str, integration_name: str):
        """Remove an integration from a project"""
        self.logger.info(f"Removing integration '{integration_name}' from project '{project_name}'")

        try:
            project = self._validate_entity_name_of_type(project_name, EntityType.PROJECT)
            integration = self._validate_entity_name_of_type(integration_name, EntityType.INTEGRATION)

            self.logger.debug(f"Removing integration {integration.name} from project {project.name}")
            self.service.remove_integration(project, integration)

            click.echo(f"✓ Removed integration '{integration.name}' from project {project.name}")
            self.logger.info("Successfully removed integration from project")

        except ValueError as e:
            self.logger.error(f"Validation error: {e}")
            click.echo(f"Error: {e}", err=True)
            raise click.ClickException(str(e))
        except Exception as e:
            self.logger.error(f"Error removing integration: {e}", exc_info=True)
            click.echo(f"Error: {e}", err=True)
            raise click.ClickException("Failed to remove integration")

    @click.command(CommandType.LIST_INTEGRATIONS.value)
    @click.argument('project_name')
    def list_integrations(self, project_name: str):
        """List all implementations for a specific project"""
        self.logger.info(f"Listing implementations for project: {project_name}")

        try:
            project = self._validate_entity_name_of_type(project_name, EntityType.PROJECT)
            integrations = self.service.get_integrations(project)

            click.echo(f"Integrations for project '{project_name}':")

            self._display_entities(integrations)

        except Exception as e:
            self.logger.error(f"Error listing project implementations: {e}", exc_info=True)
            click.echo(f"Error: {e}", err=True)
            raise click.ClickException("Failed to list project implementations")