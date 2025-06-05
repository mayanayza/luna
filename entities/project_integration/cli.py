import click

from api.cli.base import SubparserBase
from common.enums import EntityType, CommandType
from entities.integration.registry import IntegrationRegistryBase
from entities.project.registry import ProjectRegistryBase
from entities.project_integration.interface import ProjectIntegrationInterface


class ProjectIntegrationSubparserBase(SubparserBase, ProjectIntegrationInterface):
    """Project entity subparser with integration management capabilities"""

    def __init__(self, ctx):
        super().__init__(ctx)

        self.project_registry: ProjectRegistryBase = ctx.obj['registries'][EntityType.PROJECT]
        self.integration_registry: IntegrationRegistryBase = ctx.obj['registries'][EntityType.INTEGRATION]

    @click.command(CommandType.STAGE.value)
    @click.argument('project_integration_name')
    def stage(self, project_integration_name: str):
        """Stage a project through an integration"""
        self.logger.info(f"Staging '{project_integration_name}'")

        try:
            project_integration = self._validate_entity_name_of_type(project_integration_name, EntityType.PROJECT_INTEGRATION)
            self.service.stage(project_integration)

            click.echo(f"✓ Staged {project_integration.name}'")
            self.logger.info(f"Successfully staged {project_integration.name}")
        except ValueError as e:
            self.logger.error(f"Validation error: {e}")
            click.echo(f"Error: {e}", err=True)
            raise click.ClickException(str(e))
        except Exception as e:
            self.logger.error(f"Error staging project: {e}", exc_info=True)
            click.echo(f"Error: {e}", err=True)
            raise click.ClickException("Failed to stage project")


    @click.command(CommandType.PUBLISH.value)
    @click.argument('project_integration_name')
    def publish(self, project_integration_name: str):
        """Publish a project through an integration"""
        self.logger.info(f"Publishing {project_integration_name}'")

        try:
            # Get entities
            project_integration = self._validate_entity_name_of_type(project_integration_name, EntityType.PROJECT_INTEGRATION)
            self.service.publish(project_integration)

            click.echo(f"✓ Published {project_integration.name}'")
            self.logger.info(f"Successfully published {project_integration.name}")
        except ValueError as e:
            self.logger.error(f"Validation error: {e}")
            click.echo(f"Error: {e}", err=True)
            raise click.ClickException(str(e))
        except Exception as e:
            self.logger.error(f"Error publishing project: {e}", exc_info=True)
            click.echo(f"Error: {e}", err=True)
            raise click.ClickException("Failed to publish project")