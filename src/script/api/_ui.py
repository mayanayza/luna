"""
User interaction abstraction for CLI and other interfaces.
"""
import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional


class InputValidator:
    def __init__(self, validator: Callable[[str], bool], error: Dict[str, Any]):
        self._validator = validator
        self._error = error

    def validate(self, user_input) -> Dict:
        try:
            if self._validator(user_input):
                return {"passed": True}
            else:
                return {"passed": False, "error": self._error}
        except Exception as e:
            raise ValueError(f"Failed to validate input {user_input}: {e}")

class UserInterface(ABC):
    """Abstract base class for user interaction."""
    
    def __init__(self, registry_manager):
        """
        Initialize the UserInteraction.
        
        Args:
            logger: Logger instance for logging messages
        """
        self.logger = logging.getLogger(__name__)
        self._entity_type = None
        self._registry_manager = registry_manager
    
    @property
    def entity_type(self):
        return self._entity_type

    @property
    def new_entity_validators(self) -> List[InputValidator]:
        return [
            InputValidator(self.validate_input_provided, "No input detected. Please enter a name."),
            InputValidator(self.validate_not_existing_entity, f"Name already exists in {self._entity_type}s. Please enter a different name."),
            InputValidator(self.validate_kebabcase, "Input must be kebab-case (i.e. my-project-name)")
        ]

    @property
    def existing_entity_validators(self) -> List[InputValidator]:
        return [
            InputValidator(self.validate_input_provided, "No input detected. Please enter a name."),
            InputValidator(self.validate_is_existing_entity, f"Name not found in {self._entity_type}s. Please enter a different name."),
            InputValidator(self.validate_kebabcase, "Input must be kebab-case (i.e. my-project-name)")
        ]

    @property
    def emoji_validators(self) -> List[InputValidator]:
        return [
            InputValidator(self.validate_input_provided, "No input detected. Please enter a name."),
            InputValidator(self.validate_emoji, "Invalid emoji provided. Please enter a valid emoji.")
        ]

    def validate(self, user_input, validators: List[InputValidator]):
        for validator in validators:
            result = validator.validate(user_input)
            if not result['passed']:
                return result

        return {'passed': True}

    def set_context(self, context_dict: Dict[str, Any]) -> None:
        for key, val in context_dict.items():
            if f'_{key}' in vars(self):
                setattr(self, f'_{key}', val)
            else:
                self.logger.warning(f"Invalid context set by {__name__}. Key {key} does not exist.")

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

    def validate_input_provided(self, user_input: str) -> bool:
        return bool(user_input)

    def validate_not_existing_entity(self, user_input: str) -> bool:

        if self._entity_type:
            registry = self._registry_manager.get_by_name(self._entity_type)
            return False if registry.get_by_name(user_input) else True
        else:
            self.logger.error(f"Registry manager not initialized with {__name__} an't validate project existence")
            return False

    def validate_is_existing_entity(self, user_input: str) -> bool:

        if self._entity_type:
            registry = self._registry_manager.get_by_name(self._entity_type)
            return False if registry.get_by_name(user_input) else True
        else:
            self.logger.error(f"Registry manager not initialized with {__name__} an't validate project existence")
            return False

    def validate_kebabcase(self, name: str) -> bool:
        import re
        # Check if the name follows kebab-case pattern (lowercase letters, numbers, and hyphens)
        # Must start and end with alphanumeric, no consecutive hyphens
        pattern = r'^[a-z0-9]+(-[a-z0-9]+)*$'
        
        return bool(re.match(pattern, name))

    def validate_emoji(self, user_input: str) -> bool:
        import emoji
        return bool(emoji.emoji_count(user_input)) and len(user_input) == 1
    
    
    @abstractmethod
    def get_input(self, prompt: str, validators: Optional[List[InputValidator]] = [], default: Optional[str] = None) -> str:
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
    def display_entity_details(self, entity_type: str, details: Dict[str, Any]) -> None:
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
    def display_list_results(self, items: List[Any], registry_name: str) -> None:
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