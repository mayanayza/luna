from typing import List, Optional

from src.script.api._enum import CommandType
from src.script.input.input import Input, InputField
from src.script.input.validation import InputValidator


class InputFactory:
    """Factory for creating input structures"""

    @staticmethod
    def no_input_needed(handler_registry):
        return Input(
            name="no_input_needed",
            title="no_input_needed",
            command_type=None,
            entity_type=None,
            handler_registry=handler_registry,
            children=[]
        )

    @staticmethod
    def entity_target_selector_field(
        registry, 
        name: Optional[str] = None,
        allow_multiple: bool = False,
        allow_all: bool = False,
        required: bool = True,
    ) -> InputField:
        """
        Create entity selection field from registry that returns actual entities.
        
        Args:
            registry: Entity registry to get entities from
            allow_multiple: Whether to allow selecting multiple entities
            allow_all: Whether to add "All entities" option
            required: Whether selection is required
        """
        def get_entity_choices():
            """Dynamic choice function that returns dict mapping display names to entities"""
            entities = registry.get_all_entities()
            choices = {}
            
            # Add individual entity choices
            for entity in entities:
                display_name = getattr(entity, 'display_title', None) or entity.name
                choices[display_name] = [entity] if allow_multiple else entity
            
            # Add "all" option if enabled and multiple entities exist
            if allow_all and len(entities) > 1:
                choices[f"All {registry.entity_type.value}s"] = entities
            
            return choices

        field_type = List[registry.entity_class] if allow_all or allow_multiple else registry.entity_class
        
        # Determine field type based on options        
        return InputField(
            name=name if name else registry.entity_type.value,
            title=f"Select {registry.entity_type.value.title()}",
            field_type=field_type,
            required=required,
            choices=get_entity_choices,
            allow_multiple=allow_multiple,
            prompt=f"Select {registry.entity_type.value}: ",
            description=f"Choose {'one or more ' if allow_multiple else 'a '}{registry.entity_type.value}{'(s)' if allow_multiple else ''}"
        )
    
    @staticmethod
    def create_delete_input(registry, handler_registry=None, **options):
        """Create a validated delete input with entity selection"""
        
        # Use the new entity selector
        target_field = InputFactory.entity_target_selector_field(
            registry,
            allow_multiple=options.get('allow_multiple', True),
            allow_all=options.get('allow_all', True),
            required=True
        )
        
        confirmation_field = InputField(
            name="confirm",
            title="Confirm Deletion",
            field_type=bool,
            required=True,
            param_type="flag",
            short_name="y",
            prompt="Are you sure you want to delete? (y/N): ",
            validation_rules=[InputValidator.confirmation_required()]
        )
        
        return Input(
            name=f"{registry.entity_type.value}_delete",
            title=f"Delete {registry.entity_type.value.title()}",
            entity_type=registry.entity_type,
            handler_registry=handler_registry,
            command_type=CommandType.DELETE,
            children=[target_field, confirmation_field]
        )
    
    @staticmethod
    def create_choice_input(name, title, choices, required=True):
        """
        Create a validated choice input.
        
        Args:
            name: Input name
            title: Input title  
            choices: List of choice options or dict mapping display names to values
            required: Whether a choice is required
        """
        return InputField(
            name=name,
            title=title,
            field_type=str,
            required=required,
            choices=choices
        )