import logging
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
    def __init__(self, context):
        self.logger = logging.getLogger(__name__)
        self.context = context

    def validate(self, user_input, validation_rules: List[ValidationRule], level_filter: Optional[ValidationLevel] = None):
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

    def is_type(self, expected_type: Type[Any], level: ValidationLevel = ValidationLevel.CLIENT):
        """Type validation - typically client-side for UX"""
        def check(user_input):
            return isinstance(user_input, expected_type)
        return ValidationRule(check, {"message": f"Must be {expected_type.__name__}", "code": "invalid_type"}, level)

    def input_provided(self, level: ValidationLevel = ValidationLevel.CLIENT):
        """Required field validation - typically client-side for UX"""
        def check(user_input):
            return bool(user_input) and user_input != ""
        return ValidationRule(check, {"message": "This field is required", "code": "required"}, level)

    def business_rule(self, rule_func: Callable, error_msg: str, level: ValidationLevel = ValidationLevel.SERVER):
        """Business rule validation - typically server-side for security"""
        return ValidationRule(rule_func, {"message": error_msg, "code": "business_rule"}, level)

    def is_in_list(self, items: List[str], level: ValidationLevel = ValidationLevel.CLIENT):
        """Check if input is in provided list"""
        def check(user_input):
            return user_input in items
        return ValidationRule(check, {"message": f"Provided value not one of: {', '.join(items)}", "code": "invalid_choice"}, level)

    def is_new_entity(self, level: ValidationLevel = ValidationLevel.SERVER):
        """Check if entity name is new (doesn't exist in registry)"""
        def check(user_input):
            if not self.context.current_entity_registry:
                return True  # Cannot validate without context
            entity = self.context.current_entity_registry.get_by_name(user_input)
            return entity is None
        return ValidationRule(check, {"message": f"Name already exists in {self.context.entity_type}s. Please enter a different name.", "code": "entity_exists"}, level)

    def is_existing_entity(self, level: ValidationLevel = ValidationLevel.SERVER):
        """Check if entity name exists in registry"""
        def check(user_input):
            if not self.context.current_entity_registry:
                return False  # Cannot validate without context
            entity = self.context.current_entity_registry.get_by_name(user_input)
            return entity is not None
        return ValidationRule(check, {"message": f"Name not found in {self.context.entity_type}s. Please enter a different name.", "code": "entity_not_found"}, level)

    def local_path_exists(self, level: ValidationLevel = ValidationLevel.CLIENT):
        """Check if local path exists"""
        def check(user_input):
            return Path(user_input).exists()
        return ValidationRule(check, {"message": "Path not found. Please provide a valid path.", "code": "path_not_found"}, level)

    def is_kebabcase(self, level: ValidationLevel = ValidationLevel.CLIENT):
        """Check if input follows kebab-case pattern"""
        def check(user_input):
            # Check if the name follows kebab-case pattern (lowercase letters, numbers, and hyphens)
            # Must start and end with alphanumeric, no consecutive hyphens
            pattern = r'^[a-z0-9]+(-[a-z0-9]+)*$'
            return bool(re.match(pattern, user_input))
        return ValidationRule(check, {"message": "Input must be kebab-case (i.e. my-project-name)", "code": "invalid_format"}, level)

    def is_emoji(self, level: ValidationLevel = ValidationLevel.CLIENT):
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

    # Utility methods
    def format_titlecase_to_kebabcase(self, title: str) -> str:
        """Format a title into a kebab-case name."""
        clean_title = re.sub(r'[^a-zA-Z0-9\s-]', '', title)
        name = clean_title.strip().lower().replace(' ', '-')
        name = re.sub(r'-+', '-', name)
        return name

    def format_kebabcase_to_titlecase(self, name: str) -> str:
        """Convert a kebab-case string to a title-case string."""
        title = name.replace('-', ' ')
        title = ' '.join(word.capitalize() for word in title.split())
        return title