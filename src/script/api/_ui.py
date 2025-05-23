"""
User interaction abstraction for CLI and other interfaces.
"""
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


class UIContextManager:
    def __init__(self, registry_manager):

        self._entity_type = None
        self._registry_manager = registry_manager
    
    @property
    def entity_type(self):
        return self._entity_type

    @property
    def registry(self):
        if hasattr(self, '_registry_manager') and hasattr(self, '_entity_type'):
            return self._registry_manager.get_by_name(self._entity_type)
        else:
            self.logger.warning("Registry manager and entity type not set in UIContextManager")
    
    def set_context(self, context_dict: Dict[str, Any]) -> None:
        for key, val in context_dict.items():
            if f'_{key}' in vars(self):
                setattr(self, f'_{key}', val)
            else:
                self.logger.warning(f"Invalid context set by {__name__}. Key {key} does not exist.")

class EditableAttribute:
    def __init__(self, name: str, title: str, description: str, change_handler: Callable, default_value: Any, input_type: Any):
        self._name = name
        self._title = title
        self._description = description
        self._input_type = input_type

        self._value = default_value
        self._pending_value = None
        self._is_pending = False

        self._change_handler = change_handler

    def _init_value(self, value: Optional = None):
        if value:
            self._value = type(self._value)(value)
        self.change_handler(self._value, self._value)

    @property
    def change_handler(self):
        return self._change_handler

    @property
    def input_type(self):
        return self._input_type

    @property
    def description(self):
        return self._description
    
    @property
    def name(self):
        return self._name

    @property
    def is_pending(self):
        return self._is_pending
    
    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, val):
        if type(val) is type(self._value):
            self._is_pending = True
            self._pending_value = val
        else:
            TypeError(f"Can't set value of type {type(val)} on attribute {self._name}; value of type {type(self._value)} required")

    def end_edit(self):
        try:
            result = self.change_handler(self._value, self._pending_value)
            if result:
                self._value = self._pending_value
                self._pending_value = None
                self._is_pending = False
                return result
            else:
                ValueError(f"Failed to update value of {self._name} from {self._value} to {self._pending_value}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to update value of {self._name} from {self._value} to {self._pending_value}: {e}")
            return False

class ValidationRule:
    def __init__(self, validation_function: Callable[[str], bool], error: Dict[str, Any]):
        self._validation_function = validation_function
        self._error = error

    def validate(self, user_input) -> Dict:
        try:
            if self._validation_function(user_input):
                return {"passed": True}
            else:
                return {"passed": False, "error": self._error}
        except Exception as e:
            raise ValueError(f"Failed to validate input {user_input}: {e}")

class InputValidator:
    def __init__(self, context: UIContextManager):
        self.logger = logging.getLogger(__name__)
        self.context = context

    def validate(self, user_input, validators: List[ValidationRule]):
        for validator in validators:
            result = validator.validate(user_input)
            if not result['passed']:
                return result

        return {'passed': True}

    @property
    def new_entity(self) -> List[ValidationRule]:
        return [
            ValidationRule(self.input_provided, "No input detected. Please enter input."),
            ValidationRule(self.is_new_entity, f"Name already exists in {self.context.entity_type}s. Please enter a different name."),
            ValidationRule(self.is_kebabcase, "Input must be kebab-case (i.e. my-project-name)")
        ]

    @property
    def existing_entity(self) -> List[ValidationRule]:
        return [
            ValidationRule(self.input_provided, "No input detected. Please enter input."),
            ValidationRule(self.is_existing_entity, f"Name not found in {self.context.entity_type}s. Please enter a different name."),
            ValidationRule(self.is_kebabcase, "Input must be kebab-case (i.e. my-project-name)")
        ]

    @property
    def emoji(self) -> List[ValidationRule]:
        return [
            ValidationRule(self.input_provided, "No input detected. Please enter input."),
            ValidationRule(self.validate_emoji, "Invalid emoji provided. Please enter a valid emoji.")
        ]

    def local_path(self) -> List[ValidationRule]:
        return [
            ValidationRule(self.input_provided, "No input detected. Please enter input."),
            ValidationRule(self.local_path_exists, "Path not found. Please provide a valid path.")
        ]

    def item_list_match(self, items) -> List[ValidationRule]:
        return [
            ValidationRule(self.is_in_list, f"Provided value not one of: {', '.join(items)}.")
        ]

    def is_in_list(self, items):
        def in_list(self, user_input):
            return user_input in items

        return in_list

    def input_provided(self, user_input: str) -> bool:
        return bool(user_input)

    def is_new_entity(self, user_input: str) -> bool:
        entity = self.context.registry.get_by_name(user_input)
        if entity:
            return False
        return True

    def is_existing_entity(self, user_input: str) -> bool:
        return not self.is_new_entity(user_input)

    def local_path_exists(self, user_input: str) -> bool:
        return Path(user_input).exists()

    def is_kebabcase(self, name: str) -> bool:
        import re
        # Check if the name follows kebab-case pattern (lowercase letters, numbers, and hyphens)
        # Must start and end with alphanumeric, no consecutive hyphens
        pattern = r'^[a-z0-9]+(-[a-z0-9]+)*$'
        
        return bool(re.match(pattern, name))

    def validate_emoji(self, user_input: str) -> bool:
        import emoji
        return bool(emoji.emoji_count(user_input)) and len(user_input) == 1

    def format_titlecase_to_kebabcase(self, title: str) -> str:
        """
        Format a title into a kebab-case name.
        
        Args:
            title: A title-case string (e.g. 'My Project Name')
            
        Returns:
            str: Kebab-case string (e.g. 'my-project-name')
        """
        import re
        # Remove special characters, keep alphanumeric and spaces
        clean_title = re.sub(r'[^a-zA-Z0-9\s-]', '', title)
        
        # Convert to kebab-case for name
        name = clean_title.strip().lower().replace(' ', '-')
        name = re.sub(r'-+', '-', name)  # Replace multiple hyphens with single hyphen
        
        return name

    def format_kebabcase_to_titlecase(self, name: str) -> str:
        """
        Convert a kebab-case string to a title-case string.
        
        Args:
            name: The kebab-case string (e.g. 'my-project-name')
            
        Returns:
            str: A title-case string (e.g. 'My Project Name')
        """
        # Replace hyphens with spaces
        title = name.replace('-', ' ')
        
        # Title case the result (capitalize first letter of each word)
        title = ' '.join(word.capitalize() for word in title.split())
        
        return title


class UserInterface(ABC):
    """Abstract base class for user interaction."""
    
    def __init__(self, context: UIContextManager, validator: InputValidator):
        """
        Initialize the UserInteraction.
        
        Args:
            logger: Logger instance for logging messages
        """
        self.logger = logging.getLogger(__name__)
        self.context = context
        self.validator = validator

    @abstractmethod
    def get_input(self, prompt: str, validators: Optional[List[ValidationRule]] = [], default: Optional[str] = None) -> str:
        """
        Get input from the user with optional validation.
        
        Args:
            prompt: Prompt to display to the user
            validator: Optional function to validate the input
            error_message: Message to display if validation fails
            default: Default value if the user provides no input
            
        Returns:
            str: The validated input from the user or the default value
        """
        pass
    
    @abstractmethod
    def confirm(self, message: str, default: bool = False) -> bool:
        """
        Ask the user for confirmation.
        
        Args:
            message: Confirmation message to display
            default: Default value if the user provides no input
            
        Returns:
            bool: True if confirmed, False otherwise
        """
        pass
    
    # ---- Output Methods ----
    
    @abstractmethod
    def display_message(self, message: str, level: str = "info") -> None:
        """
        Display a message to the user.
        
        Args:
            message: Message to display
            level: Message level (info, warning, error)
        """
        pass
    
    @abstractmethod
    def display_key_values_list(self, entity_type: str, details: Dict[str, Any]) -> None:
        """
        Display entity details to the user.
        
        Args:
            entity_type: Type of entity (project, integration, etc.)
            details: Entity details to display
        """
        pass
    
    @abstractmethod
    def display_results(self, results: Any) -> None:
        """
        Display command execution results.
        
        Args:
            results: Results from command execution
        """
        pass
    
    @abstractmethod
    def display_results_tabular(self, items: List[Any], registry_name: str) -> None:
        """
        Display list results.
        
        Args:
            items: Items to display
            registry_name: Type of registry
        """
        pass
    
    @abstractmethod
    def display_help(self, parser: Any) -> None:
        """
        Display help information.
        
        Args:
            parser: ArgumentParser instance or other help object
        """
        pass