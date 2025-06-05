from abc import ABC
from typing import List, Type, Dict, Set
from collections import defaultdict

from api.cli.mixins import ListableSubparserMixin, EditableSubparserMixin, DiscoverableImplementationSubparserMixin, \
    CreatableImplementationSubparserMixin, \
    RenamableSubparserMixin, UserNameableSubparserMixin, DeletableSubparserMixin, CreatableSubparserMixin
from common.enums import ApplicationLayer, EntityType
from common.interfaces import Interface, CreatableInterface
from entities.mixins import UserNameablePropertyMixin, DatabasePropertyMixin, ConfigPropertyMixin, \
    ImplementationPropertyMixin, ReadOnlyNamePropertyMixin
from registries.mixins import NameIndexedRegistryMixin, DatabaseRegistryMixin, DiscoverableImplementationRegistryMixin, \
    LoadableImplementationRegistryMixin
from services.mixins import ListableServiceMixin, DiscoverableImplementationServiceMixin, \
    CreatableImplementationServiceMixin, \
    EditableServiceMixin, \
    RenamableServiceMixin, DeletableServiceMixin, CreatableServiceMixin, LoadableImplementationServiceMixin


class CapabilityDefinition:
    """Base class for capability definitions"""
    capability_dependencies: List = []  # capabilities which must be implemented alongside this capability
    interface_dependencies: List = [] # interfaces which must be implemented by some other capability alongside this capability
    mixin_dependencies: List = []  # mixins which must be implemented by some other capability alongside this capability
    # Concrete implementations for each layer
    mixins: Dict[ApplicationLayer, List] = {
        ApplicationLayer.ENTITY: [],
        ApplicationLayer.REGISTRY: [],
        ApplicationLayer.SERVICE: [],
        ApplicationLayer.CLI: [],
    }


class EntityCapabilities(ABC):
    """Base class for entity capability declarations with composition functionality"""

    # Subclasses override this to declare their capabilities
    capabilities: List[Type[CapabilityDefinition]] = []

    # Set by EntityInitializer during __init__
    entity_type: EntityType

    @classmethod
    def get_capabilities(cls) -> Dict[str, bool]:
        """Return capabilities as boolean dict for compatibility"""
        all_cap_classes = CapabilityDefinition.__subclasses__()

        result = {}
        for cap_class in all_cap_classes:
            result[cap_class.__name__] = cap_class in cls.capabilities

        return result

    @classmethod
    def get_mixins_for_layer(cls, layer: ApplicationLayer) -> List[Type]:
        """Get all mixins needed for a specific layer"""
        mixins = []
        for capability in cls.capabilities:
            layer_mixins = capability.mixins.get(layer, [])
            mixins.extend(layer_mixins)

        # Remove duplicates while preserving order
        seen = set()
        unique_mixins = []
        for mixin in mixins:
            if mixin not in seen:
                seen.add(mixin)
                unique_mixins.append(mixin)

        return unique_mixins

    @classmethod
    def create_composed_class(cls, name: str, base_class) -> Type:
        """Dynamically create a class with required mixins for this entity's capabilities"""
        mixins = cls.get_mixins_for_layer(base_class.layer)
        bases = (base_class,) + tuple(mixins)
        c = type(name, bases, {})
        c.entity_type = cls.entity_type
        c.entity_type_name = cls.entity_type.value
        return c

    @classmethod
    def _get_mixin_interfaces(cls, mixin_class: Type) -> Set[Type[Interface]]:
        """Get all Interface subclasses that a mixin implements"""
        interfaces = set()
        for base in mixin_class.__mro__:
            # Only include actual Interface subclasses, not the mixin itself
            if (issubclass(base, Interface) and
                    base != Interface and
                    base.__name__.endswith('Interface')):  # Additional safety check
                interfaces.add(base)
        return interfaces

    @classmethod
    def _validate_name_property_requirement(cls) -> List[str]:
        """Validate that entity has either ReadOnlyNamePropertyMixin or UserNameablePropertyMixin"""
        errors = []
        entity_mixins = cls.get_mixins_for_layer(ApplicationLayer.ENTITY)

        has_name_property = any(
            issubclass(mixin, (ReadOnlyNamePropertyMixin, UserNameablePropertyMixin))
            for mixin in entity_mixins
        )

        if not has_name_property:
            errors.append(
                "Entity must have a capability which implements either ReadOnlyNamePropertyMixin or UserNameablePropertyMixin"
            )

        return errors

    @classmethod
    def _validate_interface_uniqueness(cls) -> List[str]:
        """Validate that only one capability implements a given Interface"""
        errors = []
        interface_to_capabilities = defaultdict(set)

        # Map each interface to all capabilities that implement it (across all layers)
        for capability in cls.capabilities:
            for layer in ApplicationLayer:
                layer_mixins = capability.mixins.get(layer, [])
                for mixin in layer_mixins:
                    interfaces = cls._get_mixin_interfaces(mixin)
                    for interface in interfaces:
                        interface_to_capabilities[interface].add(capability)

        # Check for conflicts
        for interface, implementing_capabilities in interface_to_capabilities.items():
            if len(implementing_capabilities) > 1:
                capability_names = [cap.__name__ for cap in implementing_capabilities]
                errors.append(
                    f"Interface {interface.__name__} implemented by multiple capabilities: {', '.join(capability_names)}"
                )

        return errors

    @classmethod
    def _validate_dependencies(cls) -> List[str]:
        """Validate all dependency requirements in one pass"""
        errors = []

        # Get available capabilities, mixins, and interfaces
        available_capabilities = {cap.__name__ for cap in cls.capabilities}
        available_mixins = set()
        available_interfaces = set()

        for layer in ApplicationLayer:
            layer_mixins = cls.get_mixins_for_layer(layer)
            for mixin in layer_mixins:
                available_mixins.add(mixin.__name__)
                interfaces = cls._get_mixin_interfaces(mixin)
                for interface in interfaces:
                    available_interfaces.add(interface.__name__)

        # Validate all dependencies for each capability
        for capability in cls.capabilities:
            cap_name = capability.__name__

            # Check capability dependencies
            for dep in capability.capability_dependencies:
                if dep.__name__ not in available_capabilities:
                    errors.append(
                        f"Capability '{cap_name}' requires capability '{dep.__name__}' which is not declared"
                    )

            # Check mixin dependencies
            for mixin_dep in capability.mixin_dependencies:
                if mixin_dep.__name__ not in available_mixins:
                    errors.append(
                        f"Capability '{cap_name}' requires mixin '{mixin_dep.__name__}' which is not available"
                    )

            # Check interface dependencies
            for interface_dep in capability.interface_dependencies:
                if interface_dep.__name__ not in available_interfaces:
                    errors.append(
                        f"Capability '{cap_name}' requires interface '{interface_dep.__name__}' which is not implemented"
                    )

        return errors

    @classmethod
    def validate_capabilities(cls) -> List[str]:
        """Validate that entity class has all required properties and capability configuration is valid"""
        all_errors = []

        # Validate interface uniqueness at capability level
        all_errors.extend(cls._validate_interface_uniqueness())

        # Validate name property requirement
        all_errors.extend(cls._validate_name_property_requirement())

        # Validate all dependencies in one pass
        all_errors.extend(cls._validate_dependencies())

        return all_errors

# === CAPABILITY CLASSES ===

class ListableCapability(CapabilityDefinition):
    """Capability for entities that can be listed"""
    mixins: Dict[ApplicationLayer, List] = {
        ApplicationLayer.ENTITY: [],
        ApplicationLayer.REGISTRY: [],
        ApplicationLayer.SERVICE: [ListableServiceMixin],
        ApplicationLayer.CLI: [ListableSubparserMixin],
    }

class DatabaseCapability(CapabilityDefinition):
    """Base for capabilities that require database persistence"""
    mixins: Dict[ApplicationLayer, List] = {
        ApplicationLayer.ENTITY: [DatabasePropertyMixin],
        ApplicationLayer.REGISTRY: [DatabaseRegistryMixin],
        ApplicationLayer.SERVICE: [],
        ApplicationLayer.CLI: [],
    }


class CreatableCapability(CapabilityDefinition):
    """Capability for entities that can be created"""
    capability_dependencies = [DatabaseCapability]

    mixins: Dict[ApplicationLayer, List] = {
        ApplicationLayer.ENTITY: [ReadOnlyNamePropertyMixin],
        ApplicationLayer.REGISTRY: [NameIndexedRegistryMixin],
        ApplicationLayer.SERVICE: [CreatableServiceMixin],
        ApplicationLayer.CLI: [CreatableSubparserMixin],
    }

class DeletableCapability(CapabilityDefinition):
    """Capability for entities that can be deleted"""
    interface_dependencies = [CreatableInterface]

    mixins: Dict[ApplicationLayer, List] = {
        ApplicationLayer.ENTITY: [],
        ApplicationLayer.REGISTRY: [],
        ApplicationLayer.SERVICE: [DeletableServiceMixin],
        ApplicationLayer.CLI: [DeletableSubparserMixin],
    }


class NameableCapability(CapabilityDefinition):
    """Capability for entities with user-provided names"""
    capability_dependencies = [DatabaseCapability]

    mixins: Dict[ApplicationLayer, List] = {
        ApplicationLayer.ENTITY: [UserNameablePropertyMixin],
        ApplicationLayer.REGISTRY: [NameIndexedRegistryMixin],
        ApplicationLayer.SERVICE: [CreatableServiceMixin],
        ApplicationLayer.CLI: [UserNameableSubparserMixin],
    }


class RenamableCapability(CapabilityDefinition):
    """Capability for entities that can be renamed"""
    mixin_dependencies = [UserNameablePropertyMixin]

    mixins: Dict[ApplicationLayer, List] = {
        ApplicationLayer.ENTITY: [],
        ApplicationLayer.REGISTRY: [],
        ApplicationLayer.SERVICE: [RenamableServiceMixin],
        ApplicationLayer.CLI: [RenamableSubparserMixin],
    }


class EditableCapability(CapabilityDefinition):
    """Capability for entities with editable configuration"""
    capability_dependencies = [DatabaseCapability]

    mixins: Dict[ApplicationLayer, List] = {
        ApplicationLayer.ENTITY: [ConfigPropertyMixin],
        ApplicationLayer.REGISTRY: [],
        ApplicationLayer.SERVICE: [EditableServiceMixin],
        ApplicationLayer.CLI: [EditableSubparserMixin],
    }

class DiscoverableImplementationCapability(CapabilityDefinition):
    """Capability for discovering implementation files"""
    capability_dependencies = []

    mixins: Dict[ApplicationLayer, List] = {
        ApplicationLayer.ENTITY: [ImplementationPropertyMixin],
        ApplicationLayer.REGISTRY: [DiscoverableImplementationRegistryMixin],
        ApplicationLayer.SERVICE: [DiscoverableImplementationServiceMixin],
        ApplicationLayer.CLI: [DiscoverableImplementationSubparserMixin],
    }

class LoadableImplementationCapability(CapabilityDefinition):
    """Capability for loading entities directly from implementation files (one entity created per file)"""
    capability_dependencies = [DiscoverableImplementationCapability]

    mixins: Dict[ApplicationLayer, List] = {
        ApplicationLayer.ENTITY: [ReadOnlyNamePropertyMixin],
        ApplicationLayer.REGISTRY: [NameIndexedRegistryMixin, LoadableImplementationRegistryMixin],
        ApplicationLayer.SERVICE: [LoadableImplementationServiceMixin],
        ApplicationLayer.CLI: [],
    }

class UserNameableImplementationCapability(CapabilityDefinition):
    """Capability for creating user-named entities from implementation files"""
    capability_dependencies = [DiscoverableImplementationCapability]

    mixins: Dict[ApplicationLayer, List] = {
        ApplicationLayer.ENTITY: [UserNameablePropertyMixin],
        ApplicationLayer.REGISTRY: [NameIndexedRegistryMixin],
        ApplicationLayer.SERVICE: [CreatableImplementationServiceMixin],
        ApplicationLayer.CLI: [CreatableImplementationSubparserMixin],
    }