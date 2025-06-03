from abc import ABC

from src.script.common.enums import EntityType
import logging
import click
from typing import Type

from src.script.common.enums import CommandType
from src.script.entities.base import Entity
from src.script.registries.base import Registry
from src.script.services.base import Service


class ClickEntitySubparser(ABC):
    # Provided by EntityMixin
    entity_type: EntityType
    entity_class: type
    entity_type_name: str

    def __init__(self, ctx):
        self.ctx = ctx
        self.registry: Type[Registry] = ctx.obj['registries'][self.entity_type]
        self.service: Type[Service] = self.registry.service
        self.logger = logging.getLogger(f"{self.__class__.__name__}")

        self.logger.debug(f"Initializing {self.entity_type_name} command group")

    def get_subparser(self):
        """Create a Click group with all commands from this entity subparser instance"""

        @click.group(name=self.entity_type_name, help=f"Commands targeting {self.entity_type_name}s")
        @click.pass_context
        def entity_group(ctx):
            f"""{self.entity_type_name.title()} management commands"""
            # Store this instance in the context so commands can access it
            ctx.obj[f'{self.entity_type_name}_subparser'] = self

        # Automatically discover and add all click commands from this instance's class hierarchy
        commands_added = 0
        self.logger.debug(f"Scanning class {self.__class__.__name__} and its hierarchy for commands...")

        # Debug: Show all methods being examined
        all_methods = []
        click_methods = []

        # Look through the entire MRO (Method Resolution Order) to find Click commands
        # Replace the command detection logic with this approach:
        for cls in self.__class__.__mro__:
            self.logger.debug(f"Examining class: {cls.__name__}")
            for attr_name in dir(cls):
                if attr_name.startswith('_'):
                    continue

                try:
                    attr = getattr(cls, attr_name)

                    # Check if it's a Click Command object
                    if isinstance(attr, click.Command):
                        if attr_name not in click_methods:
                            click_methods.append(attr_name)
                            try:
                                # Get the original undecorated method from the callback
                                original_callback = attr.callback

                                # Create a wrapper that binds to self
                                # Create a wrapper that binds to self
                                def make_bound_callback(method_name, subparser_instance):
                                    def bound_callback(*args, **kwargs):
                                        logger = logging.getLogger("BoundCallback")
                                        logger.debug(f"Bound callback called for {method_name}")
                                        logger.debug(f"Subparser instance: {subparser_instance}")
                                        logger.debug(f"Args: {args}")
                                        logger.debug(f"Kwargs: {kwargs}")

                                        # Get the original callback function from the Click command
                                        click_command = getattr(subparser_instance.__class__, method_name)
                                        logger.debug(f"Click command: {click_command}")

                                        if hasattr(click_command, 'callback'):
                                            original_callback = click_command.callback
                                            logger.debug(f"Original callback: {original_callback}")

                                            # Call the original callback with the instance as self
                                            try:
                                                result = original_callback(subparser_instance, *args, **kwargs)
                                                logger.debug(f"Method call successful, result: {result}")
                                                return result
                                            except Exception as e:
                                                logger.error(f"Error calling callback {method_name}: {e}",
                                                             exc_info=True)
                                                raise
                                        else:
                                            logger.error(f"Click command {method_name} has no callback")
                                            raise AttributeError(f"Click command {method_name} has no callback")

                                    return bound_callback

                                bound_callback = make_bound_callback(attr_name, self)

                                bound_callback = make_bound_callback(attr_name, self)

                                bound_callback = make_bound_callback(attr_name, self)

                                # Create new command with bound callback
                                bound_command = click.Command(
                                    name=attr.name,
                                    callback=bound_callback,
                                    params=attr.params,
                                    help=attr.help,
                                    epilog=attr.epilog,
                                    short_help=attr.short_help,
                                    context_settings=attr.context_settings,
                                    hidden=attr.hidden,
                                    deprecated=attr.deprecated
                                )
                                entity_group.add_command(bound_command)
                                commands_added += 1
                                self.logger.debug(f"Added command: {attr_name} from class {cls.__name__}")
                            except Exception as e:
                                self.logger.error(f"Failed to add command {attr_name}: {e}")

                    # Keep track of all callable methods for debugging
                    elif callable(attr) and not attr_name.startswith('_'):
                        if attr_name not in all_methods:
                            all_methods.append(attr_name)

                except Exception as e:
                    self.logger.debug(f"Error examining {attr_name}: {e}")

        self.logger.debug(f"Added {commands_added} commands to {self.entity_type_name} group")
        return entity_group

    def get_entity_from_name(self, name: str) -> Entity | None:
        entity = self.service.get_by_name(name)
        if not entity:
            click.echo(f"No {self.entity_type_name} '{name}' found")
            return None
        return entity


class ClickListableEntitySubparser(ClickEntitySubparser, ABC):

    def _list_entities(self, entities):
        """Utility function to display entities in a formatted table"""
        try:
            from tabulate import tabulate
            headers = [
                'name',
                'uuid',
                *entities[0].fields.keys()
            ]
            rows = []

            for entity in entities:
                try:
                    rows.append([
                        entity.name,
                        entity.uuid,
                        *entity.fields.values()
                    ])
                except Exception as e:
                    self.logger.error(f"Error getting details for {self.entity_type_name} {entity.name}: {e}")
                    rows.append([entity.name, 'Error', '', '', '', ''])

            click.echo(f"Found {len(entities)} {self.entity_type_name}(s):")
            click.echo(tabulate(rows, headers=headers))

        except ImportError:
            self.logger.warning("tabulate not available")
            for entity in entities:
                click.echo(f"  - {entity.name} ({entity.uuid})")

    @click.command(CommandType.LIST.value)
    def list_entities(self):
        """List all entities with optional sorting"""
        sort = 'name'
        self.logger.info(f"Listing {self.entity_type_name} sorting on field: {sort}")

        try:
            # Use self.service instead of ctx.obj['service']
            entities = self.service.list_entities(sort_by=sort)
            self.logger.debug(f"Retrieved {len(entities)} {self.entity_type_name}(s)")

            if not entities:
                click.echo(f"No {self.entity_type_name}s found")
                return

            self._list_entities(entities)

        except Exception as e:
            self.logger.error(f"Error listing {self.entity_type_name}(s): {e}", exc_info=True)
            click.echo(f"Error: {e}", err=True)
            raise click.ClickException(f"Failed to list {self.entity_type_name}(s)")

    @click.command(CommandType.DETAIL.value)
    @click.argument('name')
    def show_entity_details(self, name: str):
        """Show detailed information about a specific entity"""
        self.logger.info(f"Showing details for {self.entity_type_name}: {name}")
        try:
            entity = self.get_entity_from_name(name)
            if not entity:
                return

            details = self.service.get_entity_details(entity)
            entity_name = details.pop('name', entity.name)
            uuid = details.pop('uuid', entity.uuid)
            self.logger.debug(f"Retrieved details for {self.entity_type_name}: {entity_name}")

            click.echo(f"{self.entity_type_name.title()} Details: {entity.name}")
            click.echo("=" * 50)
            click.echo(f"Name: {entity_name}")
            click.echo(f"UUID: {uuid}")
            for field, value in details.items():
                click.echo(f"  {field}: {value}")
        except Exception as e:
            self.logger.error(f"Error showing details for {self.entity_type_name}: {e}", exc_info=True)
            click.echo(f"Unexpected error: {e}", err=True)
            raise click.ClickException(f"Failed to show details for {self.entity_type_name}")


class ClickCreatableEntitySubparser(ClickListableEntitySubparser, ABC):
    pass


class ClickNameableEntitySubparser(ClickCreatableEntitySubparser, ABC):

    def _base_create_entity(self, name: str, emoji: str, **kwargs):
        """Call the parent create logic without Click decorators"""
        self.logger.info(f"Creating {self.entity_type_name}: {name} with emoji={emoji}")

        try:
            # Use self.service instead of accessing from context
            entity = self.service.create(name=name, emoji=emoji, **kwargs)

            click.echo(f"✓ Created {self.entity_type_name}:")
            click.echo(f"  Name: {entity.name}")
            if entity.emoji:
                click.echo(f"  Emoji: {entity.emoji}")
            click.echo(f"  ID: {entity.uuid}")

            self.logger.info(f"Successfully created {self.entity_type_name}: {name}")
            return entity

        except ValueError as e:
            self.logger.error(f"Validation error creating {self.entity_type_name}: {e}")
            click.echo(f"Error: {e}", err=True)
            raise click.ClickException(str(e))
        except Exception as e:
            self.logger.error(f"Error creating {self.entity_type_name}: {e}", exc_info=True)
            click.echo(f"Unexpected error: {e}", err=True)
            raise click.ClickException(f"Failed to create {self.entity_type_name}")

    @click.command(CommandType.CREATE.value)
    @click.argument('name')
    @click.option('--emoji', '-e', help='Entity emoji')
    def create_entity(self, name: str, emoji: str = None):
        """Create a new entity"""
        self._base_create_entity(name, emoji)

    @click.command(CommandType.DELETE.value)
    @click.argument('name')
    @click.option('--yes', '-y', is_flag=True, help='Skip confirmation prompt')
    def delete_entity(self, name: str, yes: bool):
        """Delete an entity"""
        logger = logging.getLogger(f"{self.entity_type_name}DeleteCli")
        logger.info(f"Deleting {self.entity_type_name}: {name}")
        try:
            entity = self.get_entity_from_name(name)
            if not entity:
                return

            if not yes:
                click.echo(f"This will delete {self.entity_type_name} '{entity.name}'")
                self.show_entity_details(entity.name)
                if not click.confirm("\nAre you sure you want to continue?"):
                    click.echo("Cancelled")
                    logger.info(f"{self.entity_type_name} deletion cancelled by user: {name}")
                    return

            self.service.delete(entity)
            click.echo(f"✓ Deleted {self.entity_type_name} '{name}'")
            logger.info(f"Successfully deleted {self.entity_type_name}: {name}")
        except Exception as e:
            logger.error(f"Error deleting {self.entity_type_name}: {e}", exc_info=True)
            click.echo(f"Unexpected error: {e}", err=True)
            raise click.ClickException(f"Failed to delete {self.entity_type_name}")


class ClickCreatableFromModuleEntitySubparser(ClickNameableEntitySubparser, ABC):

    @click.command(CommandType.CREATE.value)
    @click.argument('name')
    @click.argument('submodule')
    @click.option('--emoji', '-e', help='Entity emoji')
    def create_from_module(self, name: str, submodule: str, emoji: str = None):
        """Create a new entity from a specific module"""
        if not self.service.is_module(submodule):
            available_modules = self.service.list_modules()
            self.logger.error(f"Module '{submodule}' is not a valid module. Options: {available_modules}")
            click.echo(f"Error: Module '{submodule}' is not valid. Available modules: {', '.join(available_modules)}")
            return

        self._base_create_entity(name, emoji, submodule=submodule)

    @click.command(CommandType.LIST_MODULES.value)
    def list_modules(self):
        """List available modules for this entity type"""
        self.logger.info(f"Listing available {self.entity_type_name} modules")

        try:
            modules = self.service.list_modules()

            if not modules:
                click.echo(f"No {self.entity_type_name} modules found")
                return

            click.echo(f"Available {self.entity_type_name} modules:")

            # Try tabular display
            try:
                from tabulate import tabulate
                module_data = [[module] for module in modules]
                click.echo(tabulate(module_data, headers=['Module'], tablefmt='grid'))
            except ImportError:
                self.logger.warning("tabulate not available, using simple format")
                for module in modules:
                    click.echo(f"  - {module}")

            self.logger.info(f"Listed {len(modules)} {self.entity_type_name} modules")

        except Exception as e:
            self.logger.error(f"Error listing {self.entity_type_name} modules: {e}", exc_info=True)
            click.echo(f"Error: {e}", err=True)
            raise click.ClickException(f"Failed to list {self.entity_type_name} modules")