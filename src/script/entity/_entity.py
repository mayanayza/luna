from abc import abstractmethod
from datetime import datetime
from typing import Dict
from uuid import uuid4

import pytz
from src.script.api._enum import CommandType
from src.script.common.decorators import entity_quantity, register_handlers
from src.script.common.mixins import (
    ClassWithHandlers,
    Creatable,
    CreatableFromModule,
    Listable,
    Storable,
)
from src.script.entity._base import Entity
from src.script.entity._enum import EntityQuantity, EntityType, HandlerType
from src.script.input.input import Input, InputField, InputPermissions
from src.script.input.validation import InputValidator
from src.script.registry._base import Registry


class EntityWithHandlers(ClassWithHandlers):

    def _register_class_handler(self, handler_config):
        """Register handlers based on class configuration"""
        from src.script.entity.handler import Handler

        # Extract values from handler config
        command_type = handler_config['command_type']
        input_method_name = handler_config['input_method_name']
        
        # Get the source class
        source_class = self.__class__
        
        # Get the handler method from the source class
        handler_method = getattr(source_class, handler_config['handler_method_name'])
        
        # Get the input function from the source class
        if input_method_name and hasattr(source_class, input_method_name):
            input_method = getattr(source_class, input_method_name)
        else:
            input_method = None
        
        # Register the handler with the input function
        Handler(
            registry=self.handler_registry,
            handler_method=handler_method,
            input_method=input_method,
            entity_type=self.type,
            handler_type=HandlerType.SYSTEM,
            entity_registry=self.registry,
            command_type=command_type,
            source_class=source_class,
            needs_target=True
        )

 ##         ##                ##              ##        ###
 ##                           ##              ##         ##
 ##       ####      #####   ######    ######  ######     ##      #####
 ##         ##     ##         ##     ##   ##  ##   ##    ##     ##   ##
 ##         ##      ####      ##     ##   ##  ##   ##    ##     #######
 ##         ##         ##     ##     ##  ###  ##   ##    ##     ##
 ######   ######   #####       ###    ### ##  ######    ####     #####

class ListableEntity(Entity, Listable, EntityWithHandlers):
    def __init__(self, registry: 'Registry', **kwargs):
        self._handler_registry = registry.manager.get_by_entity_type(EntityType.HANDLER)

        super().__init__(registry, **kwargs)
        EntityWithHandlers.__init__(self)

  #####     ##                                ##        ###
 ##   ##    ##                                ##         ##
 ##       ######    #####   ## ###    ######  ######     ##      #####
  #####     ##     ##   ##  ###      ##   ##  ##   ##    ##     ##   ##
      ##    ##     ##   ##  ##       ##   ##  ##   ##    ##     #######
 ##   ##    ##     ##   ##  ##       ##  ###  ##   ##    ##     ##
  #####      ###    #####   ##        ### ##  ######    ####     #####


@register_handlers(
    {
        'input_method_name': 'get_detail_inputs',
        'handler_method_name': 'handle_detail',
        'command_type': CommandType.DETAIL,
    },
    {
        'input_method_name': 'get_edit_inputs',
        'handler_method_name': 'handle_edit',
        'command_type': CommandType.EDIT,
    }
)
class StorableEntity(ListableEntity, Storable, EntityWithHandlers):
    # Subclasses should define this as a list of InputField objects
    _config_fields = []
    
    def __init__(self, registry: 'Registry', **kwargs):

        super().__init__(registry, **kwargs)    

        # load_dotenv()
        
        self._uuid = kwargs.get('uuid', uuid4())
        self._date_created = kwargs.get('date_created', datetime.now(pytz.utc).isoformat())        
        
        if not hasattr(self, '_db') or getattr(self, '_db') is None:
            self._db = None
        
        self._db_fields = {}

        # Load config from DB
        db_id = kwargs.get('db_id', None)
        if db_id:
            self._db_id = db_id
            registry.set_next_id(db_id)
        else:
            self._db_id = registry.get_next_id()

        # Initialize config Input object as None - will be created on first access
        self._config_input = None
        
        # Store config data for lazy loading
        self._config_data = kwargs.get('config_data', None)

    def _initialize_config(self):
        """Initialize the config Input object from class-defined fields"""
        # Use the class-defined fields directly as children
        # The fields are defined at the subclass level and contain all the specifications
        
        try:
            # Create the Input object using the class-defined fields
            self._config_input = Input(
                name=f"{self.type.value}_config_{self.uuid}",
                title=f"Configure {self.display_title}",
                description=f"Set configuration values for the {self.type}",
                children=self._config_fields,  # Use fields defined in subclass
                handler_registry=self.handler_registry,
                permissions=getattr(self, '_config_permissions', InputPermissions())
            )

            if self._config_data:
                self._config_input.load_from_dict(self._config_data)

        except Exception as e:
            self.logger.error(f"Error creating config Input object: {e}")
            raise

    @property
    @abstractmethod
    def short_name(self):
        pass

    @property
    def display_title(self):
        return self._name.title()

    @property
    def interface(self):
        if hasattr(self, '_interface'):
            return self._interface
        else:
            NotImplementedError("No interface implemented")
            self.logger.error(f"Interface not implemented for {self.type}")

    @property
    def config(self):
        """Return the Input object containing configuration fields"""
        if self._config_input is None:
            self._initialize_config()
        return self._config_input

    @config.setter
    def config(self, val):
        """Allow setting config data as a dictionary"""
        if isinstance(val, dict):
            self._config_input.load_from_dict(val)
        else:
            raise ValueError("Config must be set as a dictionary")
    
    def get_config_value(self, field_name: str):
        """Helper method to get configuration values from form fields"""
        if self.config is None:
            return None
        child = self.config.children.get(field_name)
        if child and hasattr(child, 'value'):
            return child.value
        return None

    def set_config_value(self, field_name: str, value):
        """Helper method to set configuration values"""
        child = self.config.children.get(field_name)
        if child and isinstance(child, InputField):
            child.value = value
            child.commit_value()
        else:
            raise ValueError(f"Config field '{field_name}' not found")

    def get_config_dict(self):
        """Get configuration as a dictionary for DB storage"""
        return self.config.to_dict()

    def load_config_from_dict(self, config_data: Dict):
        """Load configuration from dictionary (e.g., from DB)"""
        self.config.load_from_dict(config_data)

    @property
    def db_id(self):
        return self._db_id
    
    @property
    def db_fields(self):
        # Include config data in db_fields for persistence
        base_fields = self._db_fields.copy()
        base_fields['config_data'] = self.get_config_dict()
        return base_fields

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

     ######                                ##
       ##                                  ##
       ##     ## ###   ######   ##   ##  ######
       ##     ###  ##  ##   ##  ##   ##    ##
       ##     ##   ##  ##   ##  ##   ##    ##
       ##     ##   ##  ##   ##  ##  ###    ##
     ######   ##   ##  ######    ### ##     ###
                       ##

    @classmethod
    def get_edit_inputs(cls, registry, handler_registry, **kwargs) -> Input:

        entity = kwargs.get(registry.entity_type.value, None)
        children = [entity.config] if entity else []

        return Input(
            name=f"{registry.entity_type.value}_edit",
            title=f"Edit {registry.entity_type.value.title()}s",
            entity_type=registry.entity_type,
            command_type=CommandType.EDIT,
            handler_registry=handler_registry,
            children=children
        )

    @classmethod
    def get_detail_inputs(cls, registry, handler_registry, **kwargs) -> Input:

        return Input(
            name=f"{registry.entity_type.value}_detail",
            title=f"{registry.entity_type.value.title()} Details",
            entity_type=registry.entity_type,
            command_type=CommandType.DETAIL,
            handler_registry=handler_registry,
            children=[]
        )

     ##   ##                         ##   ###
     ##   ##                         ##    ##
     ##   ##   ######  ## ###    ######    ##      #####   ## ###
     #######  ##   ##  ###  ##  ##   ##    ##     ##   ##  ###
     ##   ##  ##   ##  ##   ##  ##   ##    ##     #######  ##
     ##   ##  ##  ###  ##   ##  ##   ##    ##     ##       ##
     ##   ##   ### ##  ##   ##   ######   ####     #####   ##


    @classmethod
    @entity_quantity(EntityQuantity.SINGLE)
    def handle_edit(cls, registry, **kwargs):

        entity = kwargs.get(registry.entity_type.value)
        
        entity.ui.respond(f"Editing configuration for '{entity.name}'", "info")
        
        success = entity.ui.form_builder.fill_form_interactive(entity.config)
        if success:
            entity.ui.respond("Editing completed!", "success")
            # Save the updated config to database
            entity.db.upsert(entity.type, entity)
        else:
            return None

    @classmethod
    @entity_quantity(EntityQuantity.SINGLE)
    def handle_detail(cls, registry, **kwargs) -> Dict:

        entity = kwargs.get(registry.entity_type.value)

        try:
            detail = vars(entity)
            detail['_config'] = entity.config.to_dict()

            def is_object(val):
                return not isinstance(val, (str, int, float, bool, type(None), dict, list, tuple))

            def contains_object_in_list(val):
                return isinstance(val, (list, tuple)) and any(is_object(item) for item in val)

            return {
                k: v for k, v in detail.items()
                if not is_object(v) and not contains_object_in_list(v)
            }

        except Exception as e:
            entity.logger.error(f"Error getting details for entity: {e}")
            return False


   ####                                ##              ##        ###
  ##  ##                               ##              ##         ##
 ##       ## ###    #####    ######  ######    ######  ######     ##      #####
 ##       ###      ##   ##  ##   ##    ##     ##   ##  ##   ##    ##     ##   ##
 ##       ##       #######  ##   ##    ##     ##   ##  ##   ##    ##     #######
  ##  ##  ##       ##       ##  ###    ##     ##  ###  ##   ##    ##     ##
   ####   ##        #####    ### ##     ###    ### ##  ######    ####     #####


@register_handlers(
    {
        'input_method_name': 'get_delete_inputs',
        'handler_method_name': 'handle_delete',
        'command_type': CommandType.DELETE,
    },
    {
        'input_method_name': 'get_rename_inputs',
        'handler_method_name': 'handle_rename',
        'command_type': CommandType.RENAME,
    }
)
class CreatableEntity(StorableEntity, Creatable, EntityWithHandlers):
    def __init__(self, registry: 'Registry', **kwargs):
        
        super().__init__(registry, **kwargs)

        self._emoji = kwargs.get('emoji', '')
        self._title = kwargs.get('title', '')

        self._db_fields = {
            'emoji': self._emoji,
            'title': self._title,
            **self._db_fields
        }

     ######                                ##
       ##                                  ##
       ##     ## ###   ######   ##   ##  ######
       ##     ###  ##  ##   ##  ##   ##    ##
       ##     ##   ##  ##   ##  ##   ##    ##
       ##     ##   ##  ##   ##  ##  ###    ##
     ######   ##   ##  ######    ### ##     ###
                       ##
    @classmethod
    def get_delete_inputs(cls, handler_registry, registry, **kwargs) -> Input:
        """Create standard entity deletion input specification"""
        return Input(
            name=f"{registry.entity_type.value}_delete",
            title=f"Delete {registry.entity_type.value.title()}",
            entity_type=registry.entity_type,
            handler_registry=handler_registry,
            confirm_submit=False,
            command_type=CommandType.DELETE,
            children=[]
        )

    @classmethod
    def get_rename_inputs(cls, handler_registry, registry, **kwargs) -> Input:
        return Input(
            name=f"{registry.entity_type.value}_rename",
            title=f"Rename {registry.entity_type.value.title()}",
            entity_type=registry.entity_type,
            handler_registry=handler_registry,
            command_type=CommandType.RENAME,
            children=[
                InputField(
                    name="new_name",
                    title="New Name",
                    field_type=str,
                    required=True,
                    short_name="n",
                    prompt="Enter new name: ",
                    default_value=lambda value: value[registry.entity_type.value].name,
                    validation_rules=[
                        InputValidator.is_kebabcase(),
                        InputValidator.is_new_entity(registry)
                    ]
                ),
                InputField(
                    name="new_emoji",
                    title="New Emoji",
                    field_type=str,
                    required=False,
                    short_name="e",
                    prompt="Enter new emoji (or leave empty to keep current): ",
                    default_value=lambda value: value[registry.entity_type.value].emoji,
                    validation_rules=[InputValidator.is_emoji()]
                )
            ]
        )

     ##   ##                         ##   ###
     ##   ##                         ##    ##
     ##   ##   ######  ## ###    ######    ##      #####   ## ###
     #######  ##   ##  ###  ##  ##   ##    ##     ##   ##  ###
     ##   ##  ##   ##  ##   ##  ##   ##    ##     #######  ##
     ##   ##  ##  ###  ##   ##  ##   ##    ##     ##       ##
     ##   ##   ### ##  ##   ##   ######   ####     #####   ##


    @classmethod
    @abstractmethod
    def handle_delete(cls, **kwargs):
        pass

    @classmethod
    @entity_quantity(EntityQuantity.SINGLE)
    def handle_rename(cls, registry, new_emoji, new_name, **kwargs):

        entity = kwargs.get(registry.entity_type.value)

        old_name = entity.name
        old_emoji = entity.emoji
        old_title = entity.title

        entity.emoji = kwargs.get('new_emoji')
        entity.name = kwargs.get('new_name')
        entity.title = InputValidator.format_kebabcase_to_titlecase(entity.name)

        entity.registry.update_name_index(entity, old_name)

        entity.db.upsert(entity.type, entity)

        return old_name, old_emoji, old_title

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
        if self._emoji:
            return f"{self._emoji} {self._title}"
        return self._title

   ####                                ##              ##        ###              #######                             ##   ##                ##            ###
  ##  ##                               ##              ##         ##              ##                                  ##   ##                ##             ##
 ##       ## ###    #####    ######  ######    ######  ######     ##      #####   ##       ## ###    #####   ### ##   ### ###   #####    ######  ##   ##    ##      #####
 ##       ###      ##   ##  ##   ##    ##     ##   ##  ##   ##    ##     ##   ##  #####    ###      ##   ##  ## # ##  ## # ##  ##   ##  ##   ##  ##   ##    ##     ##   ##
 ##       ##       #######  ##   ##    ##     ##   ##  ##   ##    ##     #######  ##       ##       ##   ##  ## # ##  ## # ##  ##   ##  ##   ##  ##   ##    ##     #######
  ##  ##  ##       ##       ##  ###    ##     ##  ###  ##   ##    ##     ##       ##       ##       ##   ##  ## # ##  ##   ##  ##   ##  ##   ##  ##  ###    ##     ##
   ####   ##        #####    ### ##     ###    ### ##  ######    ####     #####   ##       ##        #####   ##   ##  ##   ##   #####    ######   ### ##   ####     #####


class CreatableFromModuleEntity(CreatableEntity, CreatableFromModule, EntityWithHandlers):
    def __init__(self, registry, **kwargs):
        super().__init__(registry, **kwargs)


