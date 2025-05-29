from abc import abstractmethod
from typing import Dict, List

from src.script.common.constants import CommandType, EntityType, HandlerType
from src.script.common.decorators import register_handlers
from src.script.common.mixins import (
    ClassWithHandlers,
    Creatable,
    CreatableFromModule,
    Listable,
    Storable,
)
from src.script.entity.handler import Handler
from src.script.input.input import Input, InputField
from src.script.input.validation import InputValidator
from src.script.registry._base import Registry


class RegistryWithHandlers(ClassWithHandlers):

    def _register_class_handler(self, handler_config):

        command_type = handler_config['command_type']
        input_method_name = handler_config['input_method_name']
        
        # Get the source class
        source_class = self.__class__
        
        # Get the handler method from the source class
        handler_method = getattr(source_class, handler_config['handler_method_name'])
        
        # Get the input function (not the result)
        if input_method_name and hasattr(source_class, input_method_name):
            input_method = getattr(source_class, input_method_name)
        else:
            input_method = None
        
        # Register the handler with the input function
        Handler(
            registry=self.handler_registry,
            handler_method=handler_method,
            input_method=input_method,
            handler_type=HandlerType.SYSTEM,
            entity_type=self.entity_type,
            entity_registry=self,
            command_type=command_type,
            needs_target=False
        )


 ##         ##                ##              ##        ###
 ##                           ##              ##         ##
 ##       ####      #####   ######    ######  ######     ##      #####
 ##         ##     ##         ##     ##   ##  ##   ##    ##     ##   ##
 ##         ##      ####      ##     ##   ##  ##   ##    ##     #######
 ##         ##         ##     ##     ##  ###  ##   ##    ##     ##
 ######   ######   #####       ###    ### ##  ######    ####     #####

@register_handlers(
    {
        'input_method_name': 'get_list_inputs',
        'handler_method_name': 'handle_list',
        'command_type': CommandType.LIST,
    }
)
class ListableEntityRegistry(Registry, Listable, RegistryWithHandlers):
    def __init__(self, entity_type, entity_class, manager):
        
        self.handler_registry = manager.get_by_entity_type(EntityType.HANDLER)

        super().__init__(entity_type, entity_class, manager)

        RegistryWithHandlers.__init__(self)
        
    @classmethod
    def get_list_inputs(cls, registry, handler_registry, **kwargs) -> Input:
        """Create standard entity listing input specification"""
        return Input(
            name=f"{registry.entity_type.value}_list",
            title=f"List {registry.entity_type.value.title()}s",
            entity_type=registry.entity_type,
            command_type=CommandType.LIST,
            handler_registry=handler_registry,
            children=[
                InputField(
                    name="sort_by",
                    title="Sort By",
                    field_type=str,
                    required=False,
                    short_name="s",
                    default_value="name",
                    choices=["name", "date"],
                    prompt="Sort by (name/date): "
                ),
                InputField(
                    name="filter",
                    title="Filter",
                    field_type=str,
                    required=False,
                    short_name="f",
                    prompt="Filter by name (optional): "
                )
            ]
        )

    @classmethod
    def handle_list(cls, registry, sort_by='name', **kwargs) -> List[Dict]:

        entities = registry.get_all_entities()

        if sort_by == 'name':
            sorted_entities = sorted(entities, key=lambda p: getattr(p, 'name', ''))
        elif sort_by == 'date':
            sorted_entities = sorted(entities, key=lambda p: p.date_created)
        else:
            sorted_entities = sorted(entities, key=lambda p: p.db_id)
        
        # Format result
        results = []
        for entity in sorted_entities:
            result = {
                'name': entity.name,
                'uuid': str(entity.uuid),
            }
            if hasattr(entity,'_db_fields'):
                result.update(entity._db_fields)
                result.update({'db_id': str(entity.db_id)})
            results.append(result)
        
        return results
        
  #####     ##                                ##        ###
 ##   ##    ##                                ##         ##
 ##       ######    #####   ## ###    ######  ######     ##      #####
  #####     ##     ##   ##  ###      ##   ##  ##   ##    ##     ##   ##
      ##    ##     ##   ##  ##       ##   ##  ##   ##    ##     #######
 ##   ##    ##     ##   ##  ##       ##  ###  ##   ##    ##     ##
  #####      ###    #####   ##        ### ##  ######    ####     #####

class StorableEntityRegistry(ListableEntityRegistry, Storable):
    def __init__(self, entity_type, entity_class, manager):
        
        super().__init__(entity_type, entity_class, manager)

        self._db = self.manager.db_ref

    @property
    def db(self):
        if not hasattr(self, '_db') or self._db is None:
            raise RuntimeError(f"Database reference not set for {self.__class__.__name__}")
        else:
            return self.manager.get_entity_by_ref(self._db)

    @db.setter
    def db(self, db_ref):
        self._db = db_ref

        for entity in self._entities.values():
            entity.db = db_ref

    def register_entity(self, entity):
        super().register_entity(entity)
        entity.db = self._db
            

   ####                                ##              ##        ###
  ##  ##                               ##              ##         ##
 ##       ## ###    #####    ######  ######    ######  ######     ##      #####
 ##       ###      ##   ##  ##   ##    ##     ##   ##  ##   ##    ##     ##   ##
 ##       ##       #######  ##   ##    ##     ##   ##  ##   ##    ##     #######
  ##  ##  ##       ##       ##  ###    ##     ##  ###  ##   ##    ##     ##
   ####   ##        #####    ### ##     ###    ### ##  ######    ####     #####

@register_handlers(
    {
        'input_method_name': 'get_create_inputs',
        'handler_method_name': 'handle_create',
        'command_type': CommandType.CREATE,
    },
)
class CreatableEntityRegistry(StorableEntityRegistry, Creatable, RegistryWithHandlers):
    def __init__(self, entity_type, entity_class, manager):
        super().__init__(entity_type, entity_class, manager)

    @classmethod
    def get_create_inputs(cls, registry, handler_registry, **kwargs) -> Input:
        """Create standard entity creation input specification"""
        return Input(
            name=f"{registry.entity_type.value}_create",
            title=f"Create {registry.entity_type.value.title()}",
            entity_type=registry.entity_type,
            command_type=CommandType.CREATE,
            handler_registry=handler_registry,
            children=[
                InputField(
                    name="name",
                    title="Name",
                    field_type=str,
                    required=True,
                    short_name="n",
                    prompt="Enter name: ",
                    validation_rules=[
                        InputValidator.is_kebabcase(),
                        InputValidator.is_new_entity(registry)
                    ]
                ),
                InputField(
                    name="emoji",
                    title="Emoji",
                    field_type=str,
                    required=False,
                    short_name="e",
                    prompt="Enter emoji (optional): ",
                    validation_rules=[InputValidator.is_emoji()]
                ),
                InputField(
                    name="title",
                    title="Title",
                    hidden=True,
                    field_type=str,
                    required=True,
                    default_value=lambda values: InputValidator.format_kebabcase_to_titlecase(values['name']),
                    validation_rules=[]
                ),
            ]
        )

    @classmethod
    @abstractmethod
    def handle_create(cls, **kwargs):
        pass

   ####                                ##              ##        ###              #######                             ##   ##                ##            ###
  ##  ##                               ##              ##         ##              ##                                  ##   ##                ##             ##
 ##       ## ###    #####    ######  ######    ######  ######     ##      #####   ##       ## ###    #####   ### ##   ### ###   #####    ######  ##   ##    ##      #####
 ##       ###      ##   ##  ##   ##    ##     ##   ##  ##   ##    ##     ##   ##  #####    ###      ##   ##  ## # ##  ## # ##  ##   ##  ##   ##  ##   ##    ##     ##   ##
 ##       ##       #######  ##   ##    ##     ##   ##  ##   ##    ##     #######  ##       ##       ##   ##  ## # ##  ## # ##  ##   ##  ##   ##  ##   ##    ##     #######
  ##  ##  ##       ##       ##  ###    ##     ##  ###  ##   ##    ##     ##       ##       ##       ##   ##  ## # ##  ##   ##  ##   ##  ##   ##  ##  ###    ##     ##
   ####   ##        #####    ### ##     ###    ### ##  ######    ####     #####   ##       ##        #####   ##   ##  ##   ##   #####    ######   ### ##   ####     #####

@register_handlers(
    {
        'input_method_name': 'get_create_inputs',
        'handler_method_name': 'handle_create',
        'command_type': CommandType.CREATE,
    },
    {
        'input_method_name': 'get_list_modules_inputs',
        'handler_method_name': 'handle_list_modules',
        'command_type': CommandType.LIST_MODULES,
    },
)
class CreatableFromModuleEntityRegistry(CreatableEntityRegistry, CreatableFromModule, RegistryWithHandlers):
    def __init__(self, entity_type, entity_class, manager):
        super().__init__(entity_type, entity_class, manager)

    @classmethod
    def get_list_modules_inputs(cls, registry, handler_registry, **kwargs) -> Input:
        return Input(
            name=f"{registry.entity_type.value}_list_modules",
            title=f"List {registry.entity_type.value.title()} Modules",
            command_type=CommandType.LIST_MODULES,
            handler_registry=handler_registry,
            children=[]
        )

    @classmethod
    @abstractmethod
    def handle_list_modules(cls, **kwargs):
        pass

    @classmethod
    def get_create_inputs(cls, registry, handler_registry, **kwargs) -> Input:
        """Create standard entity creation input specification"""
        return Input(
            name=f"{registry.entity_type.value}_create",
            title=f"Create {registry.entity_type.value.title()}",
            entity_type=registry.entity_type,
            command_type=CommandType.CREATE,
            handler_registry=handler_registry,
            children=[
                InputField(
                    name="module",
                    title="Module",
                    field_type=str,
                    required=True,
                    short_name="m",
                    prompt="Select module: ",
                    choices=cls.handle_list_modules(registry, **kwargs),
                ),
                InputField(
                    name="name",
                    title="Name",
                    field_type=str,
                    required=True,
                    default_value=lambda values: f"{values['module']}-",
                    short_name="n",
                    prompt="Enter name: ",
                    validation_rules=[
                        InputValidator.is_kebabcase(),
                        InputValidator.is_new_entity(registry)
                    ]
                ),
                InputField(
                    name="emoji",
                    title="Emoji",
                    field_type=str,
                    required=False,
                    short_name="e",
                    prompt="Enter emoji (optional): ",
                    validation_rules=[InputValidator.is_emoji()]
                ),
                InputField(
                    name="title",
                    title="Title",
                    hidden=True,
                    field_type=str,
                    required=True,
                    default_value=lambda values: InputValidator.format_kebabcase_to_titlecase(values['name']),
                    validation_rules=[]
                ),
            ]
        )