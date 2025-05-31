import importlib
import inspect
import logging
import pkgutil
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Type

from src.script.common.results import LoadResult


@dataclass
class ModuleInfo:
    """Information about a module containing entity classes."""
    filename: str
    module_name: str
    derived_classes: List[Type]


class RegistryLoader(ABC):
    """Abstract base class for registry entity loaders."""
    
    def __init__(self, registry):
        self.registry = registry
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
    
    @abstractmethod
    def load(self, source: str, **kwargs) -> LoadResult:
        """Load entities from the specified source."""
        pass
    
    @property
    def entity_class(self) -> Type:
        """Get the entity class from registry."""
        return self.registry.entity_class
    
    @property
    def entity_type_name(self) -> str:
        """Get the entity type name for logging."""
        return getattr(self.registry.entity_type, 'value', str(self.registry.entity_type))
    
    def _create_entity(self, entity_class: Type, **kwargs) -> Optional[Any]:
        """Create an entity instance with error handling."""
        try:
            return entity_class(self.registry, **kwargs)
        except Exception as e:
            self.logger.error(f"Error creating {entity_class.__name__}: {e}")
            return None


class RegistryModuleLoader(RegistryLoader):
    """Loads entities from Python modules containing entity classes."""
    
    def load(self, package_name: str, recursive: bool = False, **kwargs) -> LoadResult:
        """
        Load entities from modules in a package or single module.
        
        Args:
            package_name: Name of the package/module to search
            recursive: If True, recursively search nested packages
            **kwargs: Additional arguments passed to entity constructors
            
        Returns:
            LoadResult with loaded entities and metadata
        """
        modules_info = self.discover_modules(package_name, recursive)
        entities = []
        errors = []
        
        for module_info in modules_info:
            for entity_class in module_info.derived_classes:
                # Add filename to kwargs for entity creation
                entity_kwargs = {**kwargs, 'filename': module_info.filename}
                
                entity = self._create_entity(entity_class, **entity_kwargs)
                if entity:
                    entities.append(entity)
                    self.logger.debug(f"Loaded entity: {entity.name} from {module_info.module_name}")
                else:
                    error_msg = f"Failed to create {entity_class.__name__} from {module_info.module_name}"
                    errors.append(error_msg)
        
        self.logger.info(f"Loaded {len(entities)} {self.entity_type_name}(s) from modules")
        return LoadResult(entities=entities, errors=errors)
    
    def discover_modules(self, package_name: str, recursive: bool = False) -> List[ModuleInfo]:
        """
        Discover modules that contain classes derived from the entity class.
        
        Args:
            package_name: Name of the package/module to search
            recursive: If True, recursively search through all nested packages
            
        Returns:
            List of ModuleInfo objects
        """
        try:
            target = importlib.import_module(package_name)
            
            if hasattr(target, '__path__'):
                # It's a package
                if recursive:
                    return self._scan_package_recursive(target)
                else:
                    return self._scan_package(target)
            else:
                # It's a single module
                return self._scan_single_module(target)
                
        except Exception as e:
            self.logger.error(f"Error loading package/module {package_name}: {e}")
            return []
    
    def get_module_filenames(self, package_name: str, recursive: bool = False) -> List[str]:
        """Get filenames of modules that contain derived entity classes."""
        modules_info = self.discover_modules(package_name, recursive)
        return [info.filename for info in modules_info]
    
    def _scan_package(self, package) -> List[ModuleInfo]:
        """Scan a package for modules with derived classes (non-recursive)."""
        results = []
        
        for module_info in pkgutil.iter_modules(package.__path__, package.__name__ + '.'):
            module_name = module_info[1]
            
            if self._should_skip_module(module_name):
                continue
            
            module_info_obj = self._scan_module_by_name(module_name)
            if module_info_obj:
                results.append(module_info_obj)
        
        return results
    
    def _scan_package_recursive(self, package) -> List[ModuleInfo]:
        """Scan a package and all nested packages recursively."""
        results = []
        
        for importer, module_name, is_pkg in pkgutil.walk_packages(
            package.__path__, 
            package.__name__ + '.',
            onerror=lambda x: None
        ):
            if self._should_skip_module(module_name) or is_pkg:
                continue
            
            module_info_obj = self._scan_module_by_name(module_name)
            if module_info_obj:
                results.append(module_info_obj)
        
        return results
    
    def _scan_single_module(self, module) -> List[ModuleInfo]:
        """Scan a single module for derived classes."""
        module_filename = module.__name__.split('.')[-1]
        
        if module_filename.startswith('_'):
            return []
        
        derived_classes = self._find_derived_classes(module)
        
        if derived_classes:
            return [ModuleInfo(
                filename=module_filename,
                module_name=module.__name__,
                derived_classes=derived_classes
            )]
        
        return []
    
    def _scan_module_by_name(self, module_name: str) -> Optional[ModuleInfo]:
        """Scan a module by name and return ModuleInfo if it contains derived classes."""
        try:
            module = importlib.import_module(module_name)
            derived_classes = self._find_derived_classes(module)
            
            if derived_classes:
                return ModuleInfo(
                    filename=module_name.split('.')[-1],
                    module_name=module_name,
                    derived_classes=derived_classes
                )
        except Exception as e:
            self.logger.error(f"Error loading module {module_name}: {e}")
        
        return None
    
    def _find_derived_classes(self, module) -> List[Type]:
        """Find all classes in a module that inherit from the entity class."""
        derived_classes = []
        
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and 
                issubclass(obj, self.entity_class) and 
                obj is not self.entity_class and
                obj.__module__ == module.__name__):
                derived_classes.append(obj)
        
        return derived_classes
    
    def _should_skip_module(self, module_name: str) -> bool:
        """Check if a module should be skipped based on naming conventions."""
        return module_name.split('.')[-1].startswith('_')


class RegistryDatabaseLoader(RegistryLoader):
    """Loads entities from database tables."""
    
    def load(self, table_name: str, **kwargs) -> LoadResult:
        """
        Load entities from a database table.
        
        Args:
            table_name: Name of the database table to load from
            **kwargs: Additional arguments passed to entity constructors
            
        Returns:
            LoadResult with loaded entities and metadata
        """
        entity_data = self._fetch_entity_data(table_name)
        entities = []
        errors = []
        
        for data in entity_data:
            # Merge kwargs with database data (kwargs take precedence)
            entity_kwargs = {**data, **kwargs}
            
            entity = self._create_entity(self.entity_class, **entity_kwargs)
            if entity:
                entities.append(entity)
                self.logger.debug(f"Loaded entity: {entity.name} from table {table_name}")
            else:
                error_msg = f"Failed to create entity from table {table_name} with data: {data}"
                errors.append(error_msg)
        
        self.logger.info(f"Loaded {len(entities)} {self.entity_type_name}(s) from database")
        return LoadResult(entities=entities, errors=errors)
    
    def fetch_raw_data(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Fetch raw entity data from database without creating entity instances.
        
        Args:
            table_name: Name of the database table
            
        Returns:
            List of dictionaries containing entity data
        """
        return self._fetch_entity_data(table_name)
    
    def _fetch_entity_data(self, table_name: str) -> List[Dict[str, Any]]:
        """Fetch entity data from the specified database table."""
        try:
            with self.registry.db.transaction():
                table = getattr(self.registry.db.dal, table_name)
                rows = self.registry.db.dal(table).select()
            
            entity_data = []
            for entity_row in rows:
                try:
                    row_dict = entity_row.as_dict()
                    entity_data.append(row_dict)
                except Exception as e:
                    self.logger.error(f"Error converting row to dict from {table_name}: {e}")
            
            self.logger.debug(f"Fetched data for {len(entity_data)} records from {table_name}")
            return entity_data
            
        except Exception as e:
            self.logger.error(f"Error loading entity data from {table_name}: {e}")
            return []


class RegistryLoaderFactory:
    """Factory for creating appropriate loader instances."""
    
    @staticmethod
    def create_module_loader(registry) -> RegistryModuleLoader:
        """Create a module loader instance."""
        return RegistryModuleLoader(registry)
    
    @staticmethod
    def create_database_loader(registry) -> RegistryDatabaseLoader:
        """Create a database loader instance."""
        return RegistryDatabaseLoader(registry)
    
    @staticmethod
    def create_loaders(registry, 
                      include_module: bool = True, 
                      include_database: bool = True) -> Dict[str, RegistryLoader]:
        """Create a dictionary of requested loader types."""
        loaders = {}
        
        if include_module:
            loaders['module'] = RegistryModuleLoader(registry)
        
        if include_database:
            loaders['database'] = RegistryDatabaseLoader(registry)
        
        return loaders