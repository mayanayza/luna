import importlib
import inspect
import logging
import pkgutil
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Type


@dataclass
class ImplementationInfo:
    """Information about a module containing entity classes."""
    filename: str
    module_name: str
    derived_classes: List[Type]


@dataclass
class LoadResult:
    entities: List
    errors: List


class RegistryLoader(ABC):
    """Abstract base class for registry entity loaders."""

    def __init__(self, registry):
        self.registry = registry
        self.logger = logging.getLogger(f"{self.__class__.__name__}")

    @abstractmethod
    def load(self, source: str, **kwargs) -> Dict:
        """Load entities from the specified source."""
        pass

    @property
    def entity_class(self) -> Type:
        """Get the entity class from registry."""
        return self.registry.entity_class

    @property
    def entity_type_name(self) -> str:
        """Get the entity type name for logging."""
        return self.registry.entity_type_name

    def _create_entity(self, entity_class: Type, **kwargs) -> Optional[Any]:
        """Create an entity instance with error handling."""
        try:
            return entity_class(self.registry, **kwargs)
        except Exception as e:
            self.logger.error(f"Error creating {entity_class.__name__}: {e}")
            return None


class RegistryImplementationLoader(RegistryLoader):
    """Loads entities from Python modules in the 'implementations' folder relative to the calling class."""

    def load(self, submodule: Optional[str] = None, **kwargs) -> LoadResult:
        """
        Load entities from modules in the 'implementations' folder.

        Args:
            submodule: The optional submodule to load entities from.
            **kwargs: Additional arguments passed to entity constructors

        Returns:
            LoadResult with loaded entities and metadata
        """
        implementations_package = self._get_implementations_package()
        if submodule is not None:
            implementations_package = f"{implementations_package}.{submodule}"
        if not implementations_package:
            self.logger.warning("Could not find implementations package")
            return LoadResult(entities=[], errors=["Implementations package not found"])

        implementations_info = self.discover_implementations(implementations_package)
        entities = []
        errors = []

        for implementation_info in implementations_info:
            for entity_class in implementation_info.derived_classes:
                # Add filename to kwargs for entity creation
                entity_kwargs = {**kwargs, 'filename': implementation_info.filename}

                entity = self._create_entity(entity_class, **entity_kwargs)
                if entity:
                    entities.append(entity)
                    self.logger.debug(f"Loaded {self.entity_type_name}: {entity.name} from {implementation_info.module_name}")
                else:
                    error_msg = f"Failed to create {entity_class.__name__} from {implementation_info.module_name}"
                    errors.append(error_msg)

        self.logger.info(f"Loaded {len(entities)} {self.entity_type_name}(s) from implementations folder")
        return LoadResult(entities=entities, errors=errors)

    def _get_implementations_package(self) -> Optional[str]:
        """
        Get the implementations package name relative to the calling class.

        Returns:
            Package name for the implementations folder, or None if not found
        """
        try:
            # Construct the implementations package name
            implementations_package = f'entities.{self.entity_type_name}.implementations'

            # Try to import it to verify it exists
            try:
                importlib.import_module(implementations_package)
                return implementations_package
            except ImportError:
                # Try without the parent package (for cases where the calling class is in the root)
                implementations_package = "implementations"
                importlib.import_module(implementations_package)
                return implementations_package

        except Exception as e:
            self.logger.error(f"Error determining implementations package: {e}")
            return None

    def discover_implementations(self, package_name: str) -> List[ImplementationInfo]:
        """
        Discover implementations that contain classes derived from the entity class.

        Args:
            package_name: Name of the implementations package to search

        Returns:
            List of ImplementationInfo objects
        """
        try:
            target = importlib.import_module(package_name)

            if hasattr(target, '__path__'):
                # It's a package
                return self._scan_package(target)
            else:
                # It's a single module
                return self._scan_single_module(target)

        except Exception as e:
            self.logger.error(f"Error loading package/module {package_name}: {e}")
            return []

    def get_implementation_filenames(self) -> List[str]:
        """Get filenames of implementations that contain derived entity classes."""
        implementations_package = self._get_implementations_package()
        if not implementations_package:
            return []

        implementations_info = self.discover_implementations(implementations_package)
        return [info.filename for info in implementations_info]

    def _scan_package(self, package) -> List[ImplementationInfo]:
        """Scan the implementations package for implementations with derived classes."""
        results = []

        for module_info in pkgutil.iter_modules(package.__path__, package.__name__ + '.'):
            module_name = module_info[1]

            if self._should_skip_module(module_name):
                continue

            module_info_obj = self._scan_module_by_name(module_name)
            if module_info_obj:
                results.append(module_info_obj)

        return results

    def _scan_single_module(self, module) -> List[ImplementationInfo]:
        """Scan a single module for derived classes."""
        module_filename = module.__name__.split('.')[-1]

        if module_filename.startswith('_'):
            return []

        derived_classes = self._find_derived_classes(module)

        if derived_classes:
            return [ImplementationInfo(
                filename=module_filename,
                module_name=module.__name__,
                derived_classes=derived_classes
            )]

        return []

    def _scan_module_by_name(self, module_name: str) -> Optional[ImplementationInfo]:
        """Scan a module by name and return ImplementationInfo if it contains derived classes."""
        try:
            module = importlib.import_module(module_name)
            derived_classes = self._find_derived_classes(module)

            if derived_classes:
                return ImplementationInfo(
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

    @staticmethod
    def _should_skip_module(module_name: str) -> bool:
        """Check if a module should be skipped based on naming conventions."""
        return module_name.split('.')[-1].startswith('_')


class RegistryDatabaseLoader(RegistryLoader):
    """Loads entities from database tables."""

    def load(self, **kwargs) -> LoadResult:
        """
        Load entities from a database table.

        Args:
            self.entity_type_name: Name of the database table to load from
            **kwargs: Additional arguments passed to entity constructors

        Returns:
            LoadResult with loaded entities and metadata
        """
        entity_data = self._fetch_entity_data()
        entities = []
        errors = []

        for data in entity_data:
            # Merge kwargs with database data (kwargs take precedence)
            entity_kwargs = {**data, **kwargs}

            entity = self._create_entity(self.entity_class, **entity_kwargs)
            if entity:
                entities.append(entity)
                self.logger.debug(f"Loaded {self.entity_type_name}: {entity} from table {self.entity_type_name}")
            else:
                error_msg = f"Failed to create {self.entity_type_name} from table {self.entity_type_name} with data: {data}"
                errors.append(error_msg)

        self.logger.info(f"Loaded {len(entities)} {self.entity_type_name}(s) from database")
        return LoadResult(entities=entities, errors=errors)

    def _fetch_entity_data(self) -> List[Dict[str, Any]]:
        """Fetch entity data from the specified database table."""
        try:
            with self.registry.db.transaction():
                table = getattr(self.registry.db.dal, self.entity_type_name)
                rows = self.registry.db.dal(table).select()

            entity_data = []
            for entity_row in rows:
                try:
                    row_dict = entity_row.as_dict()
                    entity_data.append(row_dict)
                except Exception as e:
                    self.logger.error(f"Error converting row to dict from {self.entity_type_name}: {e}")

            self.logger.debug(f"Fetched data for {len(entity_data)} records from {self.entity_type_name}")
            return entity_data

        except Exception as e:
            self.logger.error(f"Error loading entity data from {self.entity_type_name}: {e}")
            return []


class RegistryLoaderFactory:
    """Factory for creating appropriate loader instances."""

    @staticmethod
    def create_implementation_loader(registry) -> RegistryImplementationLoader:
        """Create a module loader instance."""
        return RegistryImplementationLoader(registry)

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
            loaders['module'] = RegistryImplementationLoader(registry)

        if include_database:
            loaders['database'] = RegistryDatabaseLoader(registry)

        return loaders