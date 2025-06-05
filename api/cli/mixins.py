from abc import ABC

import click

from api.cli.base import SubparserBase
from common.enums import CommandType
from common.interfaces import ListableInterface, CreatableInterface, DeletableInterface, RenamableInterface, \
    UserNameableInterface, ImplementationDiscoveryInterface, EditableInterface


class ListableSubparserMixin(SubparserBase, ListableInterface, ABC):
    """CLI implementation of listable capability"""

    @click.command(CommandType.LIST.value)
    @click.option('--sort', default='name', help='Sort by field')
    @click.option('--filter', 'filter_name', help='Filter by name')
    def list(self, sort, filter_name):
        entities = self.service.list_entities(sort_by=sort, filter_name=filter_name)
        self._display_entities(entities)

    @click.command(CommandType.DETAIL.value)
    @click.argument('name')
    def details(self, name):
        entity = self.get_entity_from_name(name)
        if not entity:
            return
        details = self.service.get_entity_details(entity)
        self._display_entity_details(details)

class CreatableSubparserMixin(SubparserBase, CreatableInterface, ABC):
    """CLI implementation of creatable capability"""

    @click.command(CommandType.CREATE.value)
    def create(self):
        self.logger.info(f"Creating {self.entity_type_name}")
        entity = self.service.create()
        click.echo(f"✓ Created {self.entity_type.value}: {entity.name}")

class UserNameableSubparserMixin(SubparserBase, CreatableInterface, UserNameableInterface, ABC):
    """Create command for user-nameable entities"""

    @click.command(CommandType.CREATE.value)
    @click.argument('name')
    def create(self, name):
        if not self.is_valid_name(name):
            self.logger.error(f"Invalid name '{name}'")
            return
        self.logger.info(f"Creating {self.entity_type_name}: {name}")
        kwargs = {'name': name}
        entity = self.service.create(**kwargs)
        click.echo(f"✓ Created {self.entity_type.value}: {entity.name}")

class DeletableSubparserMixin(SubparserBase, DeletableInterface, ABC):
    """CLI implementation of deletable capability"""

    @click.command(CommandType.DELETE.value)
    @click.argument('name')
    @click.option('--yes', '-y', is_flag=True, help='Skip confirmation')
    def delete(self, name, yes):
        self.logger.info(f"Deleting {self.entity_type_name}: {name}")
        entity = self.get_entity_from_name(name)
        if not entity:
            return

        if not yes and not click.confirm(f"Delete {self.entity_type.value} '{name}'?"):
            click.echo("Cancelled")
            return

        self.service.delete(entity)
        click.echo(f"✓ Deleted {self.entity_type.value}: {name}")


class RenamableSubparserMixin(SubparserBase, RenamableInterface, ABC):
    """CLI implementation of renamable capability"""

    @click.command(CommandType.RENAME.value)
    @click.argument('old_name')
    @click.argument('new_name')
    def rename(self, old_name, new_name):
        entity = self.get_entity_from_name(old_name)
        if not entity:
            click.echo(f"Entity '{old_name}' not found")
            return

        if not self.is_valid_name(new_name):
            self.logger.error(f"Invalid name '{new_name}'")
            click.echo(f"<UNK> Invalid name '{new_name}'")
            return

        kwargs = {}

        result = self.service.rename(entity, new_name, **kwargs)
        click.echo(f"✓ Renamed: {result['old_name']} → {result['new_name']}")


class DiscoverableImplementationSubparserMixin(SubparserBase, ImplementationDiscoveryInterface, ABC):
    """CLI implementation of module discoverable capability"""

    def is_implementation(self, name):
        return name in self.service.list_implementations()

    @click.command(CommandType.LIST_MODULES.value)
    def list_implementations(self):
        modules = self.service.list_implementations()
        click.echo(f"Available {self.entity_type.value} modules:")
        for module in modules:
            click.echo(f"  - {module}")


class CreatableImplementationSubparserMixin(SubparserBase, CreatableInterface, UserNameableInterface, ABC):
    """Create command for module-based entities"""

    @click.command(CommandType.CREATE.value)
    @click.argument('name')
    @click.argument('implementation')
    def create(self, name, implementation):
        if not self.service.is_implementation(implementation):
            available = self.service.list_implementations()
            click.echo(f"Invalid module '{implementation}'. Available: {', '.join(available)}")
            return

        if not self.is_valid_name(name):
            self.logger.error(f"Invalid name '{name}'")
            click.echo(f"<UNK> Invalid name '{name}'")
            return

        kwargs = {'name': name, 'implementation': implementation}

        entity = self.service.create(**kwargs)
        click.echo(f"✓ Created {self.entity_type.value}: {entity.name}")


class EditableSubparserMixin(SubparserBase, EditableInterface, ABC):
    """CLI implementation of editable capability"""

    @click.command('edit')
    @click.argument('name')
    @click.option('--config', help='JSON config updates')
    def edit(self, name, config):
        entity = self.get_entity_from_name(name)
        if not entity:
            return

        if config:
            import json
            try:
                config_updates = json.loads(config)
                self.service.edit(entity, **config_updates)
                click.echo(f"✓ Updated configuration for {name}")
            except json.JSONDecodeError as e:
                click.echo(f"Invalid JSON: {e}", err=True)
        else:
            click.echo("No configuration updates provided")