import importlib
import inspect
import logging
import pkgutil
import uuid
from abc import ABC, abstractmethod
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Optional,
)

if TYPE_CHECKING:
    from src.script.entity._base import EntityBase, EntityRef
    from src.script.registry._manager import RegistryManager

class Registry(ABC):
    """
    Base registry class that manages entities of a specific type.
    """
    
    def __init__(self, name: str, entity_class: 'EntityBase'):
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self._id = None
        self._name = name
        self._entity_class = entity_class
        self._entity_class_is_storable = False
        self._entities: Dict[int, 'EntityBase'] = {}
        self._entities_by_name: Dict[str, 'EntityBase'] = {}  # Secondary index by name
        self._manager: Optional['RegistryManager'] = None
        self._next_id: int = 1

        from src.script.entity._base import ModuleEntity, StorableEntity

        if issubclass(self.entity_class, StorableEntity):
            self._db = None
            self._entity_class_is_storable = True
            
            # Use the original property from StorableEntity
            db_prop = StorableEntity.db
            
            # Create an enhanced setter that also propagates to entities
            def db_registry_setter(self, value):
                # Call the original setter
                db_prop.fset(self, value)
                
                # Propagate to all entities
                for entity in self._entities.values():
                    entity.db = value
            
            # Create a new property with the original getter but enhanced setter
            db_property = property(
                db_prop.fget,  # Keep the original getter
                db_registry_setter      # Use our enhanced setter
            )
            
            # Add the property to this class
            setattr(type(self), 'db', db_property)

        if issubclass(self.entity_class, ModuleEntity):
            pass

    @abstractmethod
    def load(self):
        # Implemented by registry to load entities and do any other necessary setup
        pass

    @property
    def entity_class_is_storable(self):
        return self._entity_class_is_storable
    
    @property
    def entity_class(self):
        return self._entity_class
    
    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, val):
        self._id = val

    @property
    def name(self):
        return self._name
    
    
    @property
    def manager(self):
        return self._manager

    @manager.setter
    def manager(self, manager: 'RegistryManager'):
        self._manager = manager

    def get_next_id(self) -> int:
        """Get the next available entity ID."""
        next_id = self._next_id
        self._next_id += 1
        return next_id
        
    def register_entity(self, entity: 'EntityBase') -> None:
        """Register an entity with this registry."""
        self._entities[entity.id] = entity

        # Give entity an ID if it doesn't have one (newly created)
        # If it has one, it's being loaded and need to ensure next ID is higher to avoid duplicate IDs
        if not hasattr(entity, '_id'):
            entity._id = self.get_next_id()
        elif entity.id >= self._next_id:
            self._next_id = entity.id + 1
        
        if self.entity_class_is_storable:
            entity.db = self.manager.get_db()
        
        # Add to name index if the entity has a name attribute
        if hasattr(entity, 'name'):
            self._entities_by_name[entity.name] = entity
        
        self.logger.debug(f"Registered entity: {getattr(entity, 'name', str(entity.id))}")
    
    def unregister_entity(self, entity: 'EntityBase') -> None:
        """Remove an entity from this registry."""
        if entity.id in self._entities:
            del self._entities[entity.id]
            
            # Remove from name index if present
            if hasattr(entity, 'name') and entity.name in self._entities_by_name:
                del self._entities_by_name[entity.name]
            
            self.logger.debug(f"Unregistered entity: {getattr(entity, 'name', str(entity.id))}")
        else:
            self.logger.warning(f"Cannot unregister entity {entity.id}, not found")
    
    def get_by_id(self, entity_id: uuid.UUID) -> Optional['EntityBase']:
        """Get an entity by its ID."""
        return self._entities.get(entity_id)
    
    def get_by_name(self, name: str) -> Optional['EntityBase']:
        """Get an entity by its name."""
        return self._entities_by_name.get(name)

    def get_by_ref(self, ref: 'EntityRef') -> 'EntityBase':
        return self._entities.get(ref.entity_id)
    
    def get_all_entities(self) -> List['EntityBase']:
        """Get all entities in this registry."""
        return list(self._entities.values())

    def find_entities(self, filter_func: Callable[['EntityBase'], bool]) -> List['EntityBase']:
        """Find entities based on a filter function."""
        return [entity for entity in self._entities.values() if filter_func(entity)]
        
    def update_name_index(self, entity, old_name):
        """
        Update the name index when an entity is renamed.
        
        Args:
            entity: The entity that was renamed
            old_name: The previous name of the entity
        """
        if old_name in self._entities_by_name:
            del self._entities_by_name[old_name]
        
        # Add with new name
        if hasattr(entity, 'name'):
            self._entities_by_name[entity.name] = entity

    def load_from_database(self, table_name: str) -> None:
        try:
            with self.db.transaction():
                table = getattr(self.db.dal, table_name)
                rows = self.db.dal(table).select()
            entities_loaded = 0
            for entity_row in rows:
                try:
                    row_dict = entity_row.as_dict()
                    # Map the database column name back to the expected attribute name
                    if 'entity_data' in row_dict:
                        row_dict['data'] = row_dict.pop('entity_data')
                    entity = self.entity_class(self, **entity_row.as_dict())
                    self.register_entity(entity)
                    entities_loaded += 1
                    self.logger.debug(f"Loaded entity: {entity.name} from table {table_name}")
                except Exception as e:
                    self.logger.error(f"Error loading entity from {table_name}: {e}")
            self.logger.info(f"Loaded {entities_loaded} {self.name}(s) from database")
        except Exception as e:
            self.logger.error(f"Error loading entities from {table_name}: {e}")
            import traceback
            traceback.print_exc()

    def load_from_module(self, package_name: str) -> None:
        """Load entities from modules in a package."""
        try:
            package = importlib.import_module(package_name)
            
            for module_info in pkgutil.iter_modules(package.__path__, package.__name__ + '.'):
                module_name = module_info[1]
                
                # Skip modules that start with underscore
                if module_name.split('.')[-1].startswith('_'):
                    continue
                
                try:
                    # Import the module
                    module = importlib.import_module(module_name)
                    
                    modules_loaded = 0
                    # Find all classes in the module that inherit from the entity class
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            issubclass(obj, self.entity_class) and 
                            obj is not self.entity_class):  # Skip the base class itself
                            try:
                                # Instantiate the entity class
                                entity = obj(self)
                                # No data to load, register immediately
                                self.register_entity(entity)
                                modules_loaded += 1
                                self.logger.debug(f"Loaded entity: {entity.name} from {module_name}")
                            except Exception as e:
                                self.logger.error(f"Error loading {name} from {module_name}: {e}")
                    self.logger.info(f"Loaded {modules_loaded} {self.name}(s) from modules")
                except Exception as e:
                    self.logger.error(f"Error loading module {module_name}: {e}")
        
        except Exception as e:
            self.logger.error(f"Error loading package {package_name}: {e}")

class CommandableRegistry(Registry):
    """
    A registry that supports command execution with cross-registry capabilities, and can access the database
    """
    
    def __init__(self, name: str, entity_class):
        super().__init__(name, entity_class)

    def handle_list(self, sort_by='name', **kwargs) -> List[Dict]:
        entities = self.get_all_entities()

        if sort_by == 'name':
            sorted_entities = sorted(entities, key=lambda p: getattr(p, 'name', ''))
        elif sort_by == 'date':
            sorted_entities = sorted(entities, key=lambda p: p.date_created)
        else:
            sorted_entities = entities
        
        # Format result
        results = []
        for entity in sorted_entities:
            result = {
                'name': entity.name,
                'id': str(entity.id)
            }
            if hasattr(entity, 'date_created'):
                result['date_created'] = entity.date_created
            results.append(result)
        
        return results

    def _invoke_handler(self, handler_owner, command: str, params: dict) -> Any:
        """
        Execute a command using reflection to find the handler method.
        
        The handler method should be named using the pattern: handle_{command}
        """

        handler_name = f"handle_{command}"

        if hasattr(handler_owner, handler_name):
            handler = getattr(handler_owner, handler_name)
            if callable(handler):
                try:
                    result = handler(**params)
                    self.logger.debug(f"Executed command '{command}' on {handler_owner}")
                    return result
                except Exception as e:
                    self.logger.error(f"Error executing command '{command}' on {handler_owner}: {e}")
                    raise
        
        self.logger.warning(f"No handler found for command '{command}' on {handler_owner}")
        return None

    def invoke_entity_handler(self, entity, command: str, params: dict) -> Any:
        return self._invoke_handler(entity, command, params)

    def invoke_registry_handler(self, command: str, params: dict) -> Any:
        return self._invoke_handler(self, command, params)
        