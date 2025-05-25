import logging
from abc import ABC
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

import pytz
from dotenv import load_dotenv
from src.script.api._form import EditableAttribute, EditableGroup, FormPermissions
from src.script.api._validation import ValidationLevel
from src.script.constants import Command, EntityType
from src.script.registry._base import Registry


class EntityRef:

    """A reference to an entity that doesn't rely on mutable attributes like name."""
    def __init__(self, entity_id: UUID, registry_id: str):
        self.entity_id = entity_id
        self.registry_id = registry_id
    
    def __eq__(self, other):
        if not isinstance(other, EntityRef):
            return False
        return self.entity_id == other.entity_id and self.registry_id == other.registry_id
    
    def __hash__(self):
        return hash((self.entity_id, self.registry_id))
    
    def __str__(self):
        return f"EntityRef {self.registry_id}:{self.entity_id}"

class EntityBase(ABC):
    """Base class for all entities in the system."""
    
    def __init__(self, registry: 'Registry', type):
        if not self._name:
            raise ValueError(f"No name provided to Entity {__name__} upon init.")
            return

        self._uuid = uuid4()
        self._type = type
        self._registry = registry
        registry.register_entity(self)
        
    def __str__(self):
        return f"{self.__class__.__name__}, name '{self._name}', id '{self._uuid}'"

    @property
    def registry(self):
        return self._registry

    @property
    def type(self):
        return self._type
    
    @property
    def logger(self):
        return self._logger
    
    @property
    def ref(self) -> EntityRef:
        """Get a reference to this entity."""
        return EntityRef(self.uuid, self.registry.uuid)

    @property
    def uuid(self):
        return self._uuid
    
    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, val):
        self._name = val

    def handle_detail(self, **kwargs) -> Dict:
        try:
            detail = vars(self)
            detail['_config'] = self.config.to_dict()

            def is_object(val):
                return not isinstance(val, (str, int, float, bool, type(None), dict, list, tuple))

            def contains_object_in_list(val):
                return isinstance(val, (list, tuple)) and any(is_object(item) for item in val)

            return {
                k: v for k, v in detail.items()
                if not is_object(v) and not contains_object_in_list(v)
            }

        except Exception as e:
            self.logger.error(f"Error getting details for entity: {e}")
            return False
    
class ModuleEntity(EntityBase):
    def __init__(self, registry: 'Registry', type, name: str):
        
        self._logger = logging.getLogger(f"{self.__class__.__name__}")

        self._uuid = registry.get_next_id()
        self._name = name

        super().__init__(registry, type)

class StorableEntity(EntityBase):
    def __init__(self, registry: 'Registry', type, **kwargs):

        self._logger = logging.getLogger(f"{self.__class__.__name__}")
        
        load_dotenv()

        self._name = kwargs.get('name', '')
        self._uuid = kwargs.get('uuid', uuid4())
        self._date_created = kwargs.get('date_created', datetime.now(pytz.utc).isoformat())        
        self._db = None

        db_id = kwargs.get('db_id', None)
        if db_id:
            self._db_id = db_id
            registry.set_next_id(db_id)

        if not hasattr(self, '_config_fields'):
            self._config_fields = []

        super().__init__(registry, type)

        config = kwargs.get('config', {})
        if config:
            self.config.load_values_from_dict(config)

    @property
    def is_configurable(self):
        return self._config.name == f"{self.type}_config_{self.uuid}"
    
    @property
    def config(self):
        return EditableGroup(
            name=f"{self.type}_config_{self.uuid}",
            title=f"Configure {self.name}",
            description=f"Set configuration values for the {self.type}",
            children=self._config_fields,
            permissions=self._config_permissions if hasattr(self,'_config_permissions') else FormPermissions()
        )

    @config.setter
    def config(self, val):
        self._config_fields = val.children
    
    def get_config_value(self, field_name: str):
        """Helper method to get configuration values from form fields"""
        child = self.config.get_child(field_name)
        if child and hasattr(child, 'value'):
            return child.value
        return None

    @property
    def db_id(self):
        return self._db_id
    
    @property
    def db_fields(self):
        return {
            'config': self.config.to_dict(),
            **self._db_fields
        }

    @property
    def date_created(self):
        return self._date_created

    @date_created.setter
    def date_created(self, val):
        self._date_created = val
    
    @property
    def db(self):
        if not hasattr(self, '_db') or self._db is None:
            raise RuntimeError(f"Database reference not set for {self.__class__.__name__}")
        else:
            return self.registry.manager.get_entity_by_ref(self._db)

    @db.setter
    def db(self, db_ref):
        self._db = db_ref

    @classmethod
    def select_form(cls, ui, entity_type: EntityType, command: Command) -> Optional[str]:
        """Create and fill a form for selecting an existing entity, return entity"""        
        form = EditableGroup(
            parent=None,
            name=f"{entity_type}_selection",
            title=f"Select {entity_type.title()} to {command.title()}",
            description=f"Choose which {entity_type} you want to {command}",
            children=[
                EditableAttribute(
                    name="entity_name",
                    title=f"{entity_type.title()} Name",
                    prompt=f"Enter the name of the {entity_type} to {command}",
                    default_value="",
                    input_type=str,
                    required=True,
                    custom_validation_rules=[ui.validator.is_kebabcase(), ui.validator.is_existing_entity(ValidationLevel.CLIENT)]
                )
            ]
        )

        entity_name = form.get_child("entity_name").value

        if not entity_name:
            return None
        
        entity = ui.context.current_entity_registry.get_by_name(entity_name)
        if not entity:
            return None

        return entity

    # def apply_config(self, config_form: EditableGroup) -> bool:
    #     """Helper to apply configuration values from form to entity config"""
    #     try:
    #         for field_name, field in config_form.children.items():
    #             if isinstance(field, EditableAttribute):
    #                 # Find corresponding config attribute and set value
    #                 for config_attr in self.config:
    #                     if config_attr.name == field_name:
    #                         config_attr.value = field.value
    #                         if hasattr(config_attr, 'commit_value'):
    #                             config_attr.commit_value()
    #                         break
    #         return True
    #     except Exception as e:
    #         self.logger.error(f"Failed to apply configuration: {e}")
    #         return False

class CreatableEntity(StorableEntity):
    def __init__(self, registry: 'Registry', type, title, emoji, **kwargs):
        self._emoji = emoji
        self._title = title

        self._db_fields = {
            'emoji': emoji,
            'title': title,
            **self._db_fields
        }

        super().__init__(registry, type, **kwargs)


    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        self._title = value

    @property
    def emoji(self):
        return self._emoji

    @emoji.setter
    def emoji(self, value):
        self._emoji = value
        
    @property
    def display_title(self):
        if self.emoji:
            return f"{self.emoji} {self.title}"
        return self.title

    @classmethod
    def create_form(self, ui, entity_type: EntityType, name_prefix: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Create and fill a streamlined form for entity creation, return extracted values"""        
        form = EditableGroup(
            parent=None,
            name=f"{entity_type}_creation",
            title=f"Create New {entity_type.title()}",
            description=f"Fill out the form to create a new {entity_type}",
            children=[
                EditableAttribute(
                    name="name",
                    title="Name",
                    prompt=f"Enter name of {entity_type} to create: " + ("" if not name_prefix else f"{name_prefix}"),
                    description=f"Name of {entity_type}",
                    default_value="",
                    input_type=str,
                    required=True,
                    custom_validation_rules=[ui.validator.is_kebabcase(), ui.validator.is_new_entity(ValidationLevel.CLIENT)]
                ),
                EditableAttribute(
                    name="emoji",
                    title="Emoji",
                    prompt="Enter an emoji prefix: ",
                    description="Emoji prefix",
                    default_value="",
                    input_type=str,
                    required=False,
                    custom_validation_rules=[ui.validator.is_emoji()]
                )
            ]
        )
        
        return {
            "name": form.get_child("name").value,
            "emoji": form.get_child("emoji").value
        } if ui.form_builder.fill_form_interactive(form) else None

    @classmethod
    def rename_form(self, ui, name_prefix: Optional[str] = None) -> Optional[Dict[str, str]]:
        """Create and fill a streamlined form for entity renaming, return new values"""        
        form = EditableGroup(
            parent=None,
            name=f"{self.type}_rename",
            title=f"Rename {self.type.title()}",
            description=f"Update name details for {self.name}",
            children=[
                EditableAttribute(
                    name="new_name",
                    title="New Name",
                    description="Enter new name: " + ("" if not name_prefix else f"{name_prefix}"),
                    default_value="",
                    input_type=str,
                    required=True,
                    custom_validation_rules=[ui.validator.is_new_entity]
                ),
                EditableAttribute(
                    name="new_emoji",
                    title="New Emoji",
                    description="Enter new emoji (or leave empty to keep current)",
                    default_value=getattr(self, 'emoji', ''),
                    input_type=str,
                    required=False,
                    custom_validation_rules=[ui.validator.is_emoji]
                )
            ]
        )
        
        return {
            "new_name": form.get_child("new_name").value,
            "new_emoji": form.get_child("new_emoji").value
        } if ui.form_builder.fill_form_interactive(form) else None

