import logging
import click
from click_shell import shell

from api.cli._help import _show_main_help
from entities.database import DatabaseSubparser
from entities.integration import IntegrationSubparser
from entities.project import ProjectSubparser
from entities.project_integration import ProjectIntegrationSubparser


@shell(prompt='Luna> ', intro='Luna CLI Interactive Session\nType "help" for commands, "exit" to quit\n', invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """Luna CLI - Project Management Tool"""

    logger = logging.getLogger("CLI")
    logger.info("Starting Luna CLI")

    try:
        # Setup context
        app_context = ctx.obj.get('app_context')
        if not app_context:
            logger.error("Application context not available in ctx.obj")
            logger.debug(f"ctx.obj contents: {ctx.obj}")
            click.echo("Error: Application context not available", err=True)
            raise click.ClickException("CLI initialization failed")

        logger.debug(f"Got application context: {app_context}")

        # Set up registries
        registries = app_context.registry_manager.registries_by_entity_type

        ctx.obj['registries'] = registries
        logger.debug(f"Set up registries: {list(registries.keys())}")

        subparsers = {}

        for subparser_class in [ProjectSubparser, IntegrationSubparser, DatabaseSubparser, ProjectIntegrationSubparser]:
            subparser = subparser_class(ctx)
            subparsers[subparser.entity_type] = subparser
            cli.add_command(subparser.get_subparser())

        # Store subparsers in context for help generation
        ctx.obj['subparsers'] = subparsers

        logger.debug("Added all command groups")

        # If no subcommand is provided, show help and enter shell mode
        if ctx.invoked_subcommand is None:
            logger.debug("No subcommand provided, showing help and entering shell mode")
            _show_main_help(ctx)

    except Exception as e:
        logger.error(f"Error in CLI initialization: {e}", exc_info=True)
        click.echo(f"CLI initialization error: {e}", err=True)
        raise