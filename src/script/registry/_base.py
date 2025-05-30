import logging
from abc import ABC
from typing import TYPE_CHECKING, Callable, Dict, List, Optional
from uuid import UUID, uuid4

from src.script.common.enums import EntityType

if TYPE_CHECKING:
    from src.script.entity._base import (
        Entity,
        EntityRef,
    )
    from src.script.registry._manager import RegistryManager

 ######                       ##                ##
 ##   ##                                        ##
 ##   ##   #####    ######  ####      #####   ######   ## ###   ##  ##
 ######   ##   ##  ##   ##    ##     ##         ##     ###      ##  ##
 ## ##    #######  ##   ##    ##      ####      ##     ##       ##  ##
 ##  ##   ##        ######    ##         ##     ##     ##        #####
 ##   ##   #####        ##  ######   #####       ###   ##           ##
                    #####                                        ####

class Registry(ABC):
    """
    Base registry class that manages entities of a specific type.
    """
    
    def __init__(self, entity_type: EntityType, entity_class: 'Entity', manager):
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self._uuid = uuid4()
        self._entity_type = entity_type
        self._entity_class = entity_class
        self._entities: Dict[int, 'Entity'] = {}
        self._entities_by_name: Dict[str, 'Entity'] = {}  # Secondary index by name
        self._manager: Optional['RegistryManager'] = manager
        self._next_id: int = 1
        self.manager.register_registry(self)

    @property
    def entity_class(self):
        return self._entity_class
    
    @property
    def uuid(self):
        return self._uuid

    @uuid.setter
    def uuid(self, val):
        self._uuid = val

    @property
    def entity_type(self):
        return self._entity_type
        
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

    def set_next_id(self, val) -> None:
        if val >= self._next_id:
            self._next_id = val+1

    def register_entity(self, entity: 'Entity') -> None:
        """Register an entity with this registry."""
        self._entities[entity.uuid] = entity
               
        # Add to name index if the entity has a name attribute
        if hasattr(entity, 'name'):
            self._entities_by_name[entity.name] = entity
        
        self.logger.debug(f"Registered entity: {entity}")
    
    def unregister_entity(self, entity: 'Entity') -> None:
        """Remove an entity from this registry."""
        if entity.uuid in self._entities:
            del self._entities[entity.uuid]
            
            # Remove from name index if present
            if hasattr(entity, 'name') and entity.name in self._entities_by_name:
                del self._entities_by_name[entity.name]
            
            self.logger.debug(f"Unregistered entity: {entity}")
        else:
            self.logger.warning(f"Cannot unregister entity {entity.uuid}, not found")
    
    def get_by_id(self, entity_id: UUID) -> Optional['Entity']:
        """Get an entity by its ID."""
        return self._entities.get(entity_id, None)
    
    def get_by_name(self, name: str) -> Optional['Entity']:
        """Get an entity by its name."""
        return self._entities_by_name.get(name, None)

    def get_by_ref(self, ref: 'EntityRef') -> 'Entity':
        return self._entities.get(ref.entity_id, None)
    
    def get_all_entities(self) -> List['Entity']:
        """Get all entities in this registry."""
        return list(self._entities.values())

    def get_all_entities_names(self) -> List[str]:
        return list(self._entities_by_name.keys())

    def find_entities(self, filter_func: Callable[['Entity'], bool]) -> List['Entity']:
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

#  ##                              ##
#  ##                              ##
#  ##        #####    ######   ######   #####   ## ###
#  ##       ##   ##  ##   ##  ##   ##  ##   ##  ###
#  ##       ##   ##  ##   ##  ##   ##  #######  ##
#  ##       ##   ##  ##  ###  ##   ##  ##       ##
#  ######    #####    ### ##   ######   #####   ##

# class RegistryLoader

# class RegistryModuleLoader:

#     def __init__(self, registry):
#         self.registry = registry
#         self.logger = logging.getLogger(f"{self.__class__.__name__}")





# class RegistryEntityLoader:

#     def __init__(self, registry):
#         self.registry = registry
#         self.logger = logging.getLogger(f"{self.__class__.__name__}")

#     def find_modules_with_derived_entity_class(self, package_name: str, recursive: bool = False) -> List[Dict[str, Any]]:
#         """
#         Find modules that contain classes derived from a base class.
#         Works with both packages (folders) and individual modules (files).
        
#         Args:
#             package_name: Name of the package/module to search (e.g., 'myapp.entities' or 'myapp.entities.local')
#             recursive: If True, recursively search through all nested packages
            
#         Returns:
#             List of dictionaries containing:
#             - 'filename': module filename without .py extension
#             - 'module_name': full dotted module name
#             - 'derived_classes': list of classes that inherit from base_class
#         """
#         results = []
        
#         try:
#             target = importlib.import_module(package_name)
            
#             # Check if it's a package (has __path__) or a module
#             if hasattr(target, '__path__'):
#                 # It's a package - iterate through its submodules
#                 if recursive:
#                     results = self._scan_package_recursive(target)
#                 else:
#                     results = self._scan_package(target)
#             else:
#                 # It's a single module - scan it directly
#                 results = self._scan_single_module(target)
                
#         except Exception as e:
#             self.logger.error(f"Error loading package/module {package_name}: {e}")
#             return []
        
#         return results

#     def _scan_package(self, package) -> List[Dict[str, Any]]:
#         """Scan a package for modules with derived classes (non-recursive)."""
#         results = []
        
#         for module_info in pkgutil.iter_modules(package.__path__, package.__name__ + '.'):
#             module_name = module_info[1]
            
#             # Skip modules that start with underscore
#             if module_name.split('.')[-1].startswith('_'):
#                 continue
            
#             try:
#                 module = importlib.import_module(module_name)
#                 derived_classes = self._find_derived_classes_in_module(module)
                
#                 if derived_classes:
#                     results.append({
#                         'filename': module_name.split('.')[-1],
#                         'module_name': module_name,
#                         'derived_classes': derived_classes
#                     })
                    
#             except Exception as e:
#                 self.logger.error(f"Error loading module {module_name}: {e}")
#                 continue
        
#         return results

#     def _scan_package_recursive(self, package) -> List[Dict[str, Any]]:
#         """Scan a package and all its nested packages recursively for modules with derived classes."""
#         results = []
        
#         # Use pkgutil.walk_packages for recursive traversal
#         for importer, module_name, is_pkg in pkgutil.walk_packages(
#             package.__path__, 
#             package.__name__ + '.',
#             onerror=lambda x: None  # Skip modules that can't be imported
#         ):
#             # Skip modules that start with underscore
#             if module_name.split('.')[-1].startswith('_'):
#                 continue
            
#             # Only process modules, not packages
#             if not is_pkg:
#                 try:
#                     module = importlib.import_module(module_name)
#                     derived_classes = self._find_derived_classes_in_module(module)
                    
#                     if derived_classes:
#                         results.append({
#                             'filename': module_name.split('.')[-1],
#                             'module_name': module_name,
#                             'derived_classes': derived_classes
#                         })
                        
#                 except Exception as e:
#                     self.logger.error(f"Error loading module {module_name}: {e}")
#                     continue
        
#         return results

#     def _scan_single_module(self, module) -> List[Dict[str, Any]]:
#         """Scan a single module for derived classes."""
#         results = []
        
#         # Skip modules that start with underscore
#         module_filename = module.__name__.split('.')[-1]
#         if module_filename.startswith('_'):
#             return results
        
#         try:
#             derived_classes = self._find_derived_classes_in_module(module)
            
#             if derived_classes:
#                 results.append({
#                     'filename': module_filename,
#                     'module_name': module.__name__,
#                     'derived_classes': derived_classes
#                 })
                
#         except Exception as e:
#             self.logger.error(f"Error scanning module {module.__name__}: {e}")
        
#         return results

#     def _find_derived_classes_in_module(self, module) -> List:
#         """Find all classes in a module that inherit from the base class."""
#         derived_classes = []
        
#         for name, obj in inspect.getmembers(module):
#             if (inspect.isclass(obj) and 
#                 issubclass(obj, self.registry.entity_class) and 
#                 obj is not self.registry.entity_class and
#                 obj.__module__ == module.__name__):  # Ensure class is defined in this module
#                 derived_classes.append(obj)
        
#         return derived_classes

#     def get_filenames_with_derived_entity_class(self, package_name: str, recursive: bool = False) -> List[str]:
#         """Get just the filenames that contain derived classes."""
#         modules_info = self.find_modules_with_derived_entity_class(package_name, recursive=recursive)
#         return [info['filename'] for info in modules_info]

#     def load_from_module(self, package_name: str, recursive: bool = False, **kwargs: Optional) -> List:
#         """Load entities from modules in a package or single module."""
#         modules_info = self.find_modules_with_derived_entity_class(package_name, recursive=recursive)
#         entities = []
        
#         for module_info in modules_info:
#             for cls in module_info['derived_classes']:
#                 try:
#                     kwargs['filename'] = module_info['filename']
#                     entity = cls(self.registry, **kwargs)
#                     entities.append(entity)
#                     self.logger.debug(f"Loaded entity: {entity.name} from {module_info['module_name']}")
#                 except Exception as e:
#                     self.logger.error(f"Error loading {cls.__name__} from {module_info['module_name']}: {e}")
        
#         self.logger.info(f"Loaded {len(entities)} {self.registry.entity_type.value}(s) from modules")
#         return entities

#     def get_entity_data_from_database(self, table_name: str):
#         try:
#             with self.registry.db.transaction():
#                 table = getattr(self.registry.db.dal, table_name)
#                 rows = self.registry.db.dal(table).select()

#             entity_data = []

#             for entity_row in rows:
#                 try:
#                     row_dict = entity_row.as_dict()
#                     entity_data.append(row_dict)
#                 except Exception as e:
#                         self.logger.error(f"Error loading entity data {table_name}: {e}")
#             self.logger.info(f"Got data for {len(entity_data)} {self.registry.entity_type.value}(s) from database")
#         except Exception as e:
#             self.logger.error(f"Error loading entity data from {table_name}: {e}")

#         return entity_data

#     def load_from_database(self, table_name):
#         entity_data = self.get_entity_data_from_database(table_name)
#         entities_loaded = 0
#         for data in entity_data:
#             try:
#                 entity = self.registry.entity_class(self.registry, **data)
#                 entities_loaded += 1
#                 self.logger.debug(f"Loaded entity: {entity.name} from table data {table_name}")
#             except Exception as e:
#                 self.logger.error(f"Error loading entity from table data {table_name}: {e}")
#         self.logger.info(f"Loaded {entities_loaded} {self.registry.entity_type.value}(s) from database")