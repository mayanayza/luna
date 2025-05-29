# 1. Base ABC for creating smart dummy objects

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict


class SmartDummy(ABC):
    """
    Base class for creating smart dummy objects that automatically provide
    reasonable defaults for any property access without manual maintenance.
    """
    
    def __init__(self, **override_values):
        """
        Initialize with optional override values for specific properties.
        
        Args:
            **override_values: Specific values to override defaults
        """
        self._overrides = override_values
        self._essential_properties = self._get_essential_properties()
        self._fallback_generators = self._get_fallback_generators()
    
    @abstractmethod
    def _get_essential_properties(self) -> Dict[str, Any]:
        """
        Return a dict of essential properties that must have specific values.
        These are properties that the code absolutely depends on.
        """
        pass
    
    def _get_fallback_generators(self) -> Dict[str, Callable]:
        """
        Return a dict of property name patterns -> generator functions.
        Override this to provide smart defaults for property patterns.
        """
        return {
            # Property name patterns and their generators
            '_id': lambda: 0,
            'id': lambda: 0,
            'name': lambda: "",
            'title': lambda: "",
            'value': lambda: "",
            'emoji': lambda: "",
            'uuid': lambda: "",
            'date': lambda: "",
            'type': lambda: self._essential_properties.get('type'),
            'config': lambda: self._create_empty_config(),
        }
    
    def _create_empty_config(self):
        """Create an empty config object for testing"""
        try:
            from src.script.input.input import Input
            return Input(
                name="dummy_config",
                title="Test Configuration", 
                children=[],
                handler_registry=None
            )
        except:
            return EmptyObject()
    
    def __getattr__(self, name: str) -> Any:
        """
        Automatically provide reasonable defaults for any property access.
        
        Priority:
        1. Override values provided in constructor
        2. Essential properties defined by subclass
        3. Pattern-based fallback generators
        4. Type-based smart defaults
        5. None as final fallback
        """
        # 1. Check override values first
        if name in self._overrides:
            return self._overrides[name]
        
        # 2. Check essential properties
        if name in self._essential_properties:
            return self._essential_properties[name]
        
        # 3. Check pattern-based fallbacks
        for pattern, generator in self._fallback_generators.items():
            if pattern in name.lower():
                return generator()
        
        # 4. Type-based smart defaults
        if name.startswith('is_') or name.startswith('has_') or name.startswith('can_'):
            return False  # Boolean flags default to False
        
        if name.endswith('_list') or name.endswith('s') and not name.endswith('_class'):
            return []  # Lists/collections default to empty
        
        if name.endswith('_dict') or name.endswith('_map'):
            return {}  # Dictionaries default to empty
        
        if name.endswith('_count') or name.endswith('_length') or name.endswith('_size'):
            return 0  # Counts default to 0
        
        if 'registry' in name.lower():
            return DummyRegistry()  # Nested registries
        
        # 5. Final fallback
        return None
    
    def __setattr__(self, name: str, value: Any) -> None:
        """Allow setting attributes normally"""
        if name.startswith('_') or name in ['_overrides', '_essential_properties', '_fallback_generators']:
            super().__setattr__(name, value)
        else:
            if not hasattr(self, '_overrides'):
                super().__setattr__(name, value)
            else:
                self._overrides[name] = value
    
    def __bool__(self) -> bool:
        """Dummy objects are always truthy"""
        return True
    
    def __str__(self) -> str:
        return f"Dummy{self.__class__.__name__}"
    
    def __repr__(self) -> str:
        return f"Dummy{self.__class__.__name__}(overrides={self._overrides})"


class EmptyObject:
    """An object that returns None for any attribute access"""
    
    def __getattr__(self, name: str) -> Any:
        return None
    
    def __bool__(self) -> bool:
        return False
    
    def __str__(self) -> str:
        return "EmptyObject"


# 2. Specific dummy implementations using the ABC

class DummyEntity(SmartDummy):
    """Smart dummy entity that provides realistic defaults"""
    
    def _get_essential_properties(self) -> Dict[str, Any]:
        entity_type = self._overrides.get('entity_type')
        return {
            'type': entity_type,
            'entity_type': entity_type,
            'name': self._overrides.get('name', ''),
            'title': self._overrides.get('title', ''),
            'emoji': self._overrides.get('emoji', ''),
            'uuid': self._overrides.get('uuid', ''),
            'db_id': self._overrides.get('db_id', 0),
            'date_created': self._overrides.get('date_created', ''),
        }
    
    def _get_fallback_generators(self) -> Dict[str, Callable]:
        base_generators = super()._get_fallback_generators()
        base_generators.update({
            'interface': lambda: DummyInterface(),
            'registry': lambda: DummyRegistry(entity_type=self.type),
            'handler': lambda: DummyHandler(),
            'db': lambda: DummyDatabase(),
        })
        return base_generators


class DummyRegistry(SmartDummy):
    """Smart dummy registry that provides realistic defaults"""
    
    def _get_essential_properties(self) -> Dict[str, Any]:
        entity_type = self._overrides.get('entity_type')
        return {
            'entity_type': entity_type,
            'entity_class': self._overrides.get('entity_class'),
        }
    
    def _get_fallback_generators(self) -> Dict[str, Callable]:
        base_generators = super()._get_fallback_generators()
        base_generators.update({
            'manager': lambda: DummyManager(),
            'entities': lambda: [],
            'handler_registry': lambda: DummyRegistry(entity_type='handler'),
        })
        return base_generators
    
    def get_all_entities(self):
        """Method that some code might call"""
        return []
    
    def get_by_id(self, entity_id):
        """Method that some code might call"""
        return DummyEntity(entity_type=self.entity_type)

class DummyHandler(SmartDummy):
    """Smart dummy handler"""
    
    def _get_essential_properties(self) -> Dict[str, Any]:
        return {}
    
    def __call__(self, *args, **kwargs):
        return None


class DummyDatabase(SmartDummy):
    """Smart dummy database"""
    
    def _get_essential_properties(self) -> Dict[str, Any]:
        return {}
    
    def upsert(self, *args, **kwargs):
        return True
    
    def transaction(self):
        return EmptyContextManager()


class DummyManager(SmartDummy):
    """Smart dummy manager"""
    
    def _get_essential_properties(self) -> Dict[str, Any]:
        return {}
    
    def get_by_entity_type(self, entity_type):
        return DummyRegistry(entity_type=entity_type)


class EmptyContextManager:
    """A context manager that does nothing"""
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


# 3. Factory for creating dummy objects

class DummyFactory:
    """Factory for creating appropriate dummy objects"""
    
    @staticmethod
    def create_entity(entity_type, **overrides):
        """Create a dummy entity with the given type"""
        return DummyEntity(entity_type=entity_type, **overrides)
    
    @staticmethod
    def create_registry(entity_type, **overrides):
        """Create a dummy registry with the given type"""
        return DummyRegistry(entity_type=entity_type, **overrides)
        
    @staticmethod
    def create_for_cli_parsing(entity_type, registry=None):
        """Create a complete set of dummy objects for CLI parsing"""
        dummy_registry = registry or DummyFactory.create_registry(entity_type)
        dummy_entity = DummyFactory.create_entity(entity_type)
        
        return {
            'entity': dummy_entity,
            'registry': dummy_registry,
            'handler_registry': DummyRegistry(entity_type='handler')
        }

 ######                       ##              ##   ##    ##       ##      ###
   ##                         ##              ##   ##    ##                ##
   ##      #####    #####   ######            ##   ##  ######   ####       ##
   ##     ##   ##  ##         ##              ##   ##    ##       ##       ##
   ##     #######   ####      ##              ##   ##    ##       ##       ##
   ##     ##           ##     ##              ##   ##    ##       ##       ##
   ##      #####   #####       ###             #####      ###   ######    ####


class TestDummyCreator:
    """Utility for creating test dummies in unit tests"""
    
    @staticmethod
    def project(name="test-project", emoji="🚀", **overrides):
        """Create a dummy project for testing"""
        from src.script.common.constants import EntityType
        return DummyFactory.create_entity(
            EntityType.PROJECT,
            name=name,
            emoji=emoji,
            **overrides
        )
    
    @staticmethod
    def integration(name="test-integration", **overrides):
        """Create a dummy integration for testing"""
        from src.script.common.constants import EntityType
        return DummyFactory.create_entity(
            EntityType.INTEGRATION,
            name=name,
            **overrides
        )
    
    @staticmethod
    def registry(entity_type, **overrides):
        """Create a dummy registry for testing"""
        return DummyFactory.create_registry(entity_type, **overrides)


# 6. Example usage in tests

# def test_example():
#     """Example of how to use the dummy objects in tests"""
    
#     # Create test objects easily
#     project = TestDummyCreator.project(name="my-project", emoji="🎯")
#     registry = TestDummyCreator.registry(EntityType.PROJECT)
    
#     # These will all work without throwing AttributeError
#     print(project.name)              # "my-project"
#     print(project.some_random_prop)  # None
#     print(project.is_active)         # False (boolean pattern)
#     print(project.related_items)     # [] (list pattern)
#     print(project.config.children)   # Works because config is auto-created
    
#     # Registry works too
#     print(registry.entity_type)      # EntityType.PROJECT
#     print(registry.some_method())    # None (any method call)
#     print(registry.nested_objects)   # [] (auto-default)


# 7. Decorator for automatic dummy injection (optional)

def with_dummies(entity_type):
    """Decorator that automatically injects dummy objects for missing parameters"""
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Auto-create missing common parameters
            if 'entity' not in kwargs or kwargs['entity'] is None:
                kwargs['entity'] = DummyFactory.create_entity(entity_type)
            
            if 'registry' not in kwargs or kwargs['registry'] is None:
                kwargs['registry'] = DummyFactory.create_registry(entity_type)

            return func(*args, **kwargs)
        return wrapper
    return decorator


# Usage example:
# @with_dummies(EntityType.PROJECT)
# def get_project_inputs(entity, registry, validator, **kwargs):
#     # entity, registry, validator are guaranteed to exist and be safe
#     return Input(name=f"{entity.type.value}_something", ...)