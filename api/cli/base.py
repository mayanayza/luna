import logging
from typing import Type

import click
from abc import ABC

from common.enums import EntityType, ApplicationLayer
from registries.base import Registry
from services.base import Service


class SubparserBase(ABC):
    """Minimal CLI base"""

    layer = ApplicationLayer.CLI

    def __init__(self, ctx):
        self.ctx = ctx
        self.registry: Type[Registry] = ctx.obj['registries'][self.entity_type]
        self.service: Type[Service] = self.registry.service
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self.logger.debug(f"Initializing {self.entity_type_name} command group")

    def get_subparser(self):
        """Build CLI group with only relevant commands"""

        @click.group(name=self.entity_type.value)
        def entity_group(ctx):
            pass

        # Add commands based on mixed-in capabilities
        for command in self._get_available_commands():
            entity_group.add_command(command)

        return entity_group

    def _get_available_commands(self):
        """Get commands based on mixed-in CLI capabilities"""
        commands = []
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if isinstance(attr, click.Command) and callable(attr):
                commands.append(attr)
        return commands

    def _display_entities(self, entities):
        """Display entities in table format"""
        try:
            from tabulate import tabulate
            if not entities:
                click.echo(f"No {self.entity_type.value}s found")
                return

            headers = ['name', 'uuid'] + list(entities[0].fields.keys())
            rows = []
            for entity in entities:
                row = [entity.name, str(entity.uuid)] + list(entity.fields.values())
                rows.append(row)

            click.echo(tabulate(rows, headers=headers))
        except ImportError:
            for entity in entities:
                click.echo(f"  - {entity.name} ({entity.uuid})")

    def _display_entity_details(self, details):
        """Display single entity details"""
        for key, value in details.items():
            click.echo(f"{key}: {value}")

    def _validate_entity_name_of_type(self, entity_name, entity_type):
        entity_registry: Registry = self.registry.manager.get_by_entity_type[entity_type]
        entity = entity_registry.get_by_name(entity_name)
        if not entity:
            options = entity_registry.get_all_entities_names()
            click.echo(f"No {self.entity_type.value} '{entity_name}' found")
            click.echo(f"Options: {options}")
            raise ValueError(f"Integration '{entity_name}' not found. Available: {options}")
            return None
        return entity

    def get_entity_from_name(self, name):
        """Helper to get entity by name given in args with error handling"""
        if hasattr(self.service, 'get_by_name'):
            entity = self.service.get_by_name(name)
            if not entity:
                click.echo(f"No {self.entity_type.value} '{name}' found")
                return None
            return entity
        else:
            click.echo(f"Cannot lookup by name for {self.entity_type.value}")
            return None