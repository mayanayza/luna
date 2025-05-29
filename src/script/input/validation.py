import re
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type


class ValidationMode(Enum):
    ON_SET = "on_set"
    ON_SUBMIT = "on_submit"


class ValidationLevel(Enum):
    CLIENT = "client"  # UX validation - runs on frontend for immediate feedback
    SERVER = "server"  # Business/security validation - authoritative, cannot be circumvented
    BOTH = "both"     # Runs on both client and server


class ValidationRule:
    def __init__(self, validation_function: Callable[[str], bool], error: Dict[str, Any], level: ValidationLevel = ValidationLevel.BOTH):
        self._validation_function = validation_function
        self._error = error
        self._level = level

    @property
    def level(self) -> ValidationLevel:
        return self._level

    def validate(self, user_input) -> Dict:
        try:
            if self._validation_function(user_input):
                return {"passed": True}
            else:
                return {"passed": False, "error": self._error}
        except Exception as e:
            raise ValueError(f"Failed to validate input {user_input}: {e}")

class InputValidator:
    
    @staticmethod
    def validate(user_input, validation_rules: List[ValidationRule], context: Dict = {}, level_filter: Optional[ValidationLevel] = None):
        """Validate input with optional level filtering for client/server separation"""
        filtered_rules = validation_rules
        if level_filter:
            filtered_rules = [rule for rule in validation_rules 
                            if rule.level == level_filter or rule.level == ValidationLevel.BOTH]
        
        for rule in filtered_rules:
            result = rule.validate(user_input)
            if not result['passed']:
                return result
        return {'passed': True}

    @staticmethod
    def input_provided(level: ValidationLevel = ValidationLevel.CLIENT):
        """Required field validation - typically client-side for UX"""
        def check(user_input):
            return bool(user_input) and user_input != ""
        return ValidationRule(check, {"message": "This field is required", "code": "required"}, level)

    @staticmethod
    def is_type(expected_type: Type[Any], level: ValidationLevel = ValidationLevel.CLIENT):
        """Type validation - typically client-side for UX"""
        def check(user_input):
            # Handle subscripted generics (e.g., List[str], Optional[str])
            from typing import get_origin
            
            # Get the origin type (e.g., list from List[str], or the type itself if not subscripted)
            origin_type = get_origin(expected_type) or expected_type
            
            return isinstance(user_input, origin_type) or not user_input
        
        # Get a clean name for the error message
        type_name = getattr(expected_type, '__name__', str(expected_type))
        
        return ValidationRule(check, {"message": f"Must be {type_name}", "code": "invalid_type"}, level)

    @staticmethod
    def confirmation_required(level: ValidationLevel = ValidationLevel.CLIENT):
        """Type validation - typically client-side for UX"""
        def check(user_input):
            return user_input is True
        return ValidationRule(check, {"message": "Confirmation is required", "code": "required"}, level)

    @staticmethod
    def is_kebabcase(level: ValidationLevel = ValidationLevel.CLIENT):
        """Check if input follows kebab-case pattern"""
        import re
        def check(user_input):
            pattern = r'^[a-z0-9]+(-[a-z0-9]+)*$'
            return bool(re.match(pattern, user_input))
        return ValidationRule(check, {"message": "Input must be kebab-case (i.e. my-project-name)", "code": "invalid_format"}, level)

    @staticmethod
    def is_emoji(level: ValidationLevel = ValidationLevel.CLIENT):
        """Validate emoji input"""
        def check(user_input):
            try:
                import emoji
                if user_input:
                    return bool(emoji.emoji_count(user_input)) and len(user_input) == 1
                else:
                    return True
            except ImportError:
                # If emoji library not available, accept any single character
                return len(user_input) == 1
        return ValidationRule(check, {"message": "Invalid emoji provided. Please enter a valid emoji.", "code": "invalid_emoji"}, level)

    @staticmethod
    def local_path_exists(level: ValidationLevel = ValidationLevel.CLIENT):
        """Check if local path exists"""
        def check(user_input):
            return Path(user_input).exists()
        return ValidationRule(check, {"message": "Path not found. Please provide a valid path.", "code": "path_not_found"}, level)

    @staticmethod
    def is_new_entity(registry, level: ValidationLevel = ValidationLevel.SERVER):
        """Check if entity name is new (doesn't exist in registry)"""
        def check(user_input):
            if not registry:
                return False  # Cannot validate without context
            entity = registry.get_by_name(user_input)
            return entity is None
        return ValidationRule(check, {"message": f"Name already exists in {registry.entity_type.value}s. Please enter a different name.", "code": "entity_exists"}, level)

    @staticmethod
    def is_existing_entity(registry, level: ValidationLevel = ValidationLevel.SERVER):
        """Check if entity name exists in registry"""
        def check(user_input):
            if not registry:
                return True  # Cannot validate without context
            entity = registry.get_by_name(user_input)
            return entity is not None
        return ValidationRule(check, {"message": f"Name not found in {registry.entity_type.value}s. Please enter a different name.", "code": "entity_not_found"}, level)

    # Utility methods
    @staticmethod
    def format_titlecase_to_kebabcase(title: str) -> str:
        """Format a title into a kebab-case name."""
        clean_title = re.sub(r'[^a-zA-Z0-9\s-]', '', title)
        name = clean_title.strip().lower().replace(' ', '-')
        name = re.sub(r'-+', '-', name)
        return name

    @staticmethod
    def format_kebabcase_to_titlecase(name: str) -> str:
        """Convert a kebab-case string to a title-case string."""
        title = name.replace('-', ' ')
        title = ' '.join(word.capitalize() for word in title.split())
        return title