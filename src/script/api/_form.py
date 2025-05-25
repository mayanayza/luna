import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Type

from src.script.api._validation import (
    InputValidator,
    ValidationLevel,
    ValidationMode,
    ValidationRule,
)


class FormPermissions:
    """Simple data container for form modification permissions"""
    def __init__(self, 
                 can_add_fields: bool = False,
                 can_remove_fields: bool = False,
                 can_modify_structure: bool = False,
                 can_change_handlers: bool = False):
        self.can_add_fields = can_add_fields
        self.can_remove_fields = can_remove_fields
        self.can_modify_structure = can_modify_structure
        self.can_change_handlers = can_change_handlers
    
    def to_dict(self) -> Dict[str, bool]:
        return {
            "can_add_fields": self.can_add_fields,
            "can_remove_fields": self.can_remove_fields,
            "can_modify_structure": self.can_modify_structure,
            "can_change_handlers": self.can_change_handlers
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, bool]) -> 'FormPermissions':
        return cls(
            can_add_fields=data.get("can_add_fields", False),
            can_remove_fields=data.get("can_remove_fields", False),
            can_modify_structure=data.get("can_modify_structure", False),
            can_change_handlers=data.get("can_change_handlers", False)
        )


class Editable(ABC):
    def __init__(self, 
                 name: str,
                 parent: Optional['Editable'] = None,
                 title: Optional[str] = '', 
                 description: Optional[str] = '', 
                 system_handler_ref: Optional[str] = None,
                 user_defined_handler_ref: Optional[str] = None,
                 validation_mode: ValidationMode = ValidationMode.ON_SUBMIT,
                 permissions: Optional[FormPermissions] = None,
                 max_nesting_level: Optional[int] = None):
        self._name = name
        self._title = title or name.replace('_', ' ').title()
        self._description = description
        self._parent = parent
        self._system_handler_ref = system_handler_ref
        self._user_defined_handler_ref = user_defined_handler_ref
        self._validation_mode = validation_mode
        self._permissions = permissions or FormPermissions()
        self._max_nesting_level = max_nesting_level or (parent.max_nesting_level if parent else 2)
        
        # Handler registry will be set by FormBuilder
        self._handler_registry = None
        
        # Actual handler callables (resolved from registry)
        self._system_handler: Optional[Callable] = None
        self._user_defined_handler: Optional[Callable] = None
        
        self.logger = logging.getLogger(__name__)
    
    def set_parent(self, parent: 'Editable') -> None:
        """Set or change the parent of this editable element"""
        old_parent = self._parent
        self._parent = parent
        
        # Update max nesting level if parent has one set
        if parent and parent.max_nesting_level:
            self._max_nesting_level = parent.max_nesting_level
        
        # Validate nesting level if we now have a parent
        if parent and self.level > self.max_nesting_level:
            self._parent = old_parent  # Restore old parent
            raise ValueError(f'Maximum nesting level ({self.max_nesting_level}) exceeded. Current level would be: {self.level}')
        
        # Propagate handler registry if parent has one
        if parent and parent.handler_registry:
            self.set_handler_registry(parent.handler_registry)
    
    @property
    def description(self) -> str:
        return self._description
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def title(self) -> str:
        return self._title
    
    @property
    def parent(self) -> Optional['Editable']:
        return self._parent
    
    @property
    def level(self) -> int:
        return 0 if self._parent is None else self._parent.level + 1
    
    @property
    def root_parent(self) -> 'Editable':
        """Get the top-level parent (root of the form tree)"""
        return self if self._parent is None else self._parent.root_parent
    
    @property
    def max_nesting_level(self) -> int:
        """Get the maximum nesting level for this form"""
        return self._max_nesting_level
    
    @property
    def system_handler_ref(self) -> Optional[str]:
        return self._system_handler_ref
    
    @system_handler_ref.setter
    def system_handler_ref(self, handler_ref: Optional[str]):
        self._system_handler_ref = handler_ref
        self._resolve_system_handler()
    
    @property
    def user_defined_handler_ref(self) -> Optional[str]:
        return self._user_defined_handler_ref
    
    @user_defined_handler_ref.setter
    def user_defined_handler_ref(self, handler_ref: Optional[str]):
        self._user_defined_handler_ref = handler_ref
        self._resolve_user_defined_handler()
    
    @property
    def system_handler(self) -> Optional[Callable]:
        return self._system_handler
    
    @property
    def user_defined_handler(self) -> Optional[Callable]:
        return self._user_defined_handler
    
    @property
    def handler_registry(self):
        return self._handler_registry
    
    def set_handler_registry(self, registry):
        """Set handler registry and resolve handler callables"""
        self._handler_registry = registry
        self._resolve_system_handler()
        self._resolve_user_defined_handler()
        
        # Propagate to children
        if hasattr(self, '_children'):
            for child in self._children.values():
                child.set_handler_registry(registry)
    
    def _resolve_system_handler(self):
        """Resolve system handler ref to callable"""
        if self._system_handler_ref and self._handler_registry:
            handler = self._handler_registry.get_by_ref(self._system_handler_ref)
            if handler:
                self._system_handler = handler
            else:
                self.logger.warning(f"System handler '{self._system_handler_ref}' not found in registry")
                self._system_handler = None
        else:
            self._system_handler = None
    
    def _resolve_user_defined_handler(self):
        """Resolve user-defined handler ref to callable"""
        if self._user_defined_handler_ref and self._handler_registry:
            handler = self._handler_registry.get_by_ref(self._user_defined_handler_ref)
            if handler:
                self._user_defined_handler = handler
            else:
                self.logger.warning(f"User-defined handler '{self._user_defined_handler_ref}' not found in registry")
                self._user_defined_handler = None
        else:
            self._user_defined_handler = None
    
    @property
    def permissions(self) -> FormPermissions:
        return self._permissions
    
    @permissions.setter
    def permissions(self, permissions: FormPermissions):
        self._permissions = permissions
    
    @property
    def validation_mode(self) -> ValidationMode:
        return self._validation_mode
    
    @validation_mode.setter
    def validation_mode(self, mode: ValidationMode):
        self._validation_mode = mode
    
    def invoke_handlers(self, *args, **kwargs) -> List[Any]:
        """Invoke both system-defined and user-defined handlers"""
        results = []
        
        # Invoke system-defined handler
        if self._system_handler:
            try:
                result = self._system_handler(*args, **kwargs)
                results.append({"type": "system", "handler": self._system_handler_ref, "result": result})
            except Exception as e:
                self.logger.error(f"System handler '{self._system_handler_ref}' failed for {self._name}: {e}")
                results.append({"type": "system", "handler": self._system_handler_ref, "error": str(e)})
        
        # Invoke user-defined handler
        if self._user_defined_handler:
            try:
                result = self._user_defined_handler(*args, **kwargs)
                results.append({"type": "user_defined", "handler": self._user_defined_handler_ref, "result": result})
            except Exception as e:
                self.logger.error(f"User-defined handler '{self._user_defined_handler_ref}' failed for {self._name}: {e}")
                results.append({"type": "user_defined", "handler": self._user_defined_handler_ref, "error": str(e)})
        
        return results
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Serialize object to dictionary for JSON storage"""
        pass

class EditableGroup(Editable):
    def __init__(self, 
                 name: str,
                 children: Optional[List[Editable]] = [],
                 title: Optional[str] = '',
                 **kwargs):
        # Validate handler restrictions before calling super().__init__
        proposed_system_handler = kwargs.get('system_handler_ref')
        proposed_user_handler = kwargs.get('user_defined_handler_ref')
                
        if (proposed_system_handler or proposed_user_handler) and self._has_group_children(children):
            raise ValueError('EditableGroup cannot have handlers when it contains other EditableGroup children')
        
        super().__init__(name=name, title=title, **kwargs)
        self._children = {}
        
        # Validate nesting level for this group
        if self.level > self.max_nesting_level:
            self.logger.error(f'Cannot nest Editable more than {self.max_nesting_level} levels deep. Current level: {self.level}')
            raise ValueError(f'Maximum nesting level ({self.max_nesting_level}) exceeded')
        
        # Set up children with proper parent assignment
        for child in children:
            self.add_child(child)
    
    def _has_group_children(self, children: List[Editable]) -> bool:
        """Check if any children are EditableGroup instances"""
        return any(isinstance(child, EditableGroup) for child in children)
    
    def _is_leaf_group(self) -> bool:
        """Check if this group only contains EditableAttribute children (leaf group)"""
        return all(isinstance(child, EditableAttribute) for child in self._children.values())
    
    @property
    def children(self) -> Dict[str, Editable]:
        return self._children.copy()
    
    def get_child(self, name: str) -> Optional[Editable]:
        return self._children.get(name)
    
    def validate_structure_modification(self, operation: str, child: Optional[Editable] = None) -> Dict[str, Any]:
        """Validate if a structural modification is allowed (for API validation)"""
        if operation == "add":
            if not self._permissions.can_add_fields:
                return {"allowed": False, "reason": "Adding fields not permitted"}
            if child and isinstance(child, EditableGroup) and not self._permissions.can_modify_structure:
                return {"allowed": False, "reason": "Adding groups not permitted"}
            if (self._system_handler_ref or self._user_defined_handler_ref) and isinstance(child, EditableGroup):
                return {"allowed": False, "reason": "Cannot add group to group with handlers"}
            if child and child.name in self._children:
                return {"allowed": False, "reason": f"Child '{child.name}' already exists"}
        
        elif operation == "remove":
            if not self._permissions.can_remove_fields:
                return {"allowed": False, "reason": "Removing fields not permitted"}
        
        return {"allowed": True}

    def user_add_child(self, child: Editable) -> None:
        validation = self.validate_structure_modification("add", child)
        if not validation["allowed"]:
            self.logger.error(validation["reason"])
            return
        else:
            self.add_child(child)

    def user_remove_child(self, child: Editable) -> None:
        validation = self.validate_structure_modification("remove")
        if not validation["allowed"]:
            self.logger.error(validation["reason"])
            return
        else:
            self.remove_child(child)
    
    def add_child(self, child: Editable) -> None:
        # Set this group as the child's parent
        child.set_parent(self)
        
        # Propagate handler registry if we have one
        if self._handler_registry:
            child.set_handler_registry(self._handler_registry)
        
        # Validate handler conflicts for individual children
        if isinstance(child, EditableAttribute) and (child._system_handler_ref or child._user_defined_handler_ref):
            if self._system_handler_ref or self._user_defined_handler_ref:
                self.logger.error('EditableGroup and EditableAttribute children cannot both have handlers set.')
        
        self._children[child.name] = child
    
    def remove_child(self, name: str) -> None:
        if name in self._children:
            # Clear the parent reference
            self._children[name].set_parent(None)
            del self._children[name]
            return
        self.logger.error(f"Child '{name}' not found")
    
    def get_addable_child_types(self) -> List[str]:
        """Get list of child types that can be added (for UI)"""
        if not self._permissions.can_add_fields:
            return []
        
        types = ["EditableAttribute"]
        if self._permissions.can_modify_structure and not (self._system_handler_ref or self._user_defined_handler_ref):
            types.append("EditableGroup")
        return types
    
    def validate_all(self, validator: InputValidator, level_filter: Optional[ValidationLevel] = None) -> Dict[str, Any]:
        """Validate all children with optional level filtering"""
        results = {"passed": True, "errors": {}}
        
        for name, child in self._children.items():
            if isinstance(child, EditableAttribute):
                result = child.validate(validator, level_filter=level_filter)
                if not result["passed"]:
                    results["passed"] = False
                    results["errors"][name] = result["error"]
            elif isinstance(child, EditableGroup):
                result = child.validate_all(validator, level_filter=level_filter)
                if not result["passed"]:
                    results["passed"] = False
                    results["errors"][name] = result["errors"]
        
        return results
    
    def invoke_handler(self) -> List[Any]:
        """Invoke handler with child values as named arguments (for leaf groups only)"""
        if not self._is_leaf_group():
            raise ValueError('Handler can only be invoked on leaf groups (containing only EditableAttribute children)')
        
        kwargs = {}
        for name, child in self._children.items():
            if isinstance(child, EditableAttribute):
                kwargs[name] = {'old_value': child.value, 'new_value': child.pending_value}
        
        return self.invoke_handlers(**kwargs)
    
    def commit_all_values(self, validator: InputValidator) -> bool:
        """Commit all pending values in children"""
        success = True
        for child in self._children.values():
            if isinstance(child, EditableAttribute):
                if not child.commit_value(validator):
                    success = False
            elif isinstance(child, EditableGroup):
                if not child.commit_all_values(validator):
                    success = False
        return success
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "EditableGroup",
            "name": self._name,
            "title": self._title,
            "children": {name: child.to_dict() for name, child in self._children.items()}
        }
        
    def load_values_from_dict(self, data: Dict[str, Any]):            
        children_data = data.get("children", {})
        for name, child in self._children.items():
            if name in children_data:
                child_data = children_data[name]
                if isinstance(child, EditableAttribute):
                    child.load_value_from_dict(child_data)
                elif isinstance(child, EditableGroup):
                    child.load_values_from_dict(child_data)


class EditableAttribute(Editable):
    def __init__(self, 
                 name: str,
                 default_value: Any, 
                 input_type: Type[Any], 
                 prompt: Optional[str] = None,
                 required: bool = False, 
                 custom_validation_rules: Optional[List[ValidationRule]] = None,
                 **kwargs):
        super().__init__(name=name, **kwargs)
        
        self._input_type = input_type
        self._required = required
        self._prompt = prompt
        self._custom_validation_rules = custom_validation_rules or []
        self._pending_value = None
        self._is_pending = False
        
        try:
            self._value = self._input_type(default_value) if default_value is not None else None
        except (ValueError, TypeError) as e:
            self.logger.error(f"Failed to convert default value {default_value} to {input_type}: {e}")
            self._value = None
    
    def _setup_validation(self, validator: InputValidator) -> List[ValidationRule]:
        """Set up complete validation rules including defaults and custom rules"""
        rules = []
        
        # Required field validation (client-side for UX)
        if self._required:
            rules.append(validator.input_provided(ValidationLevel.CLIENT))
        
        # Type validation (client-side for UX)
        if self._input_type:
            rules.append(validator.is_type(self._input_type, ValidationLevel.CLIENT))
        
        # Add custom validation rules
        rules.extend(self._custom_validation_rules)
        
        return rules
    
    def add_business_rule(self, validator: InputValidator, rule_func: Callable, error_msg: str):
        """Add server-side business rule validation"""
        self._custom_validation_rules.append(
            validator.business_rule(rule_func, error_msg, ValidationLevel.SERVER)
        )
    
    @property
    def required(self) -> bool:
        return self._required
    
    @property
    def prompt(self):
        return self._prompt

    @property
    def input_type(self) -> Type[Any]:
        return self._input_type
    
    @property
    def is_pending(self) -> bool:
        return self._is_pending
    
    @property
    def value(self) -> Any:
        return self._value

    @property
    def pending_value(self):
        return self._pending_value
    
    @value.setter
    def value(self, val: Any):
        """Set value with optional validation based on validation_mode"""
        self._is_pending = True
        self._pending_value = val
    
    def validate(self, validator: InputValidator, value: Any = None, level_filter: Optional[ValidationLevel] = None) -> Dict[str, Any]:
        """Validate a value with optional level filtering"""
        test_value = value if value is not None else self._value
        validation_rules = self._setup_validation(validator)
        return validator.validate(test_value, validation_rules, level_filter)
    
    def commit_value(self, validator: InputValidator) -> bool:
        """Commit pending value to actual value"""
        if not self._is_pending:
            return True
        
        try:
            # Always run full validation on commit (both client and server rules)
            validation_result = self.validate(validator, self._pending_value)
            if not validation_result["passed"]:
                self.logger.error(f"Validation failed for {self._name}: {validation_result['error']}")
                return False
            
            # Commit the value - no change handler approval needed
            self._value = self._pending_value
            self._pending_value = None
            self._is_pending = False
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to commit value for {self._name}: {e}")
            return False
    
    def rollback_value(self):
        """Rollback pending changes"""
        self._pending_value = None
        self._is_pending = False
    
    def invoke_handler(self) -> List[Any]:
        """Invoke handler with current value"""
        return self.invoke_handlers(old_value=self.value, new_value=self.pending_value)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "EditableAttribute",
            "name": self._name,
            "value": self._value,
        }
        
    def load_value_from_dict(self, data: Dict[str, Any]):
        """Load value from serialized data into existing attribute (preserves handlers and validation)"""
        if "value" in data:
            try:
                self._value = self._input_type(data["value"]) if data["value"] is not None else None
                self._pending_value = None
                self._is_pending = False
            except (ValueError, TypeError) as e:
                self.logger.error(f"Failed to load value {data['value']} for {self._name}: {e}")


# Form Builder Architecture - Primary input handler
class FormBuilder(ABC):
    """Abstract base class for platform-specific form builders - primary input handler"""
    
    def __init__(self, validator: InputValidator, handler_registry=None):
        self.validator = validator
        self.handler_registry = handler_registry
        self.editing_state = {}  # Client-side editing state
        self.pending_changes = {}  # Client-side pending changes
        self.logger = logging.getLogger(__name__)
    
    def set_form_handler_registry(self, form: EditableGroup):
        """Set handler registry for entire form tree"""
        form.set_handler_registry(self.handler_registry)
    
    @abstractmethod
    def render_form(self, form: EditableGroup) -> Any:
        """Render the form in platform-specific format"""
        pass
    
    @abstractmethod
    def render_field(self, field: EditableAttribute) -> Any:
        """Render a single field"""
        pass
    
    @abstractmethod
    def get_user_input(self, field: EditableAttribute) -> Any:
        """Get user input for a field"""
        pass
    
    @abstractmethod
    def show_validation_error(self, field_name: str, error: Dict[str, Any]):
        """Display validation error to user"""
        pass
    
    @abstractmethod
    def get_selection(self, options: List[str], default: Optional[str] = None) -> Optional[str]:
        """Get user selection from a list of options"""
        pass
    
    @abstractmethod
    def confirm(self, message: str, default: bool = False) -> bool:
        """Get confirmation from user"""
        pass
    
    @abstractmethod
    def fill_form_interactive(self, form: EditableGroup) -> bool:
        """Fill form interactively and handle submission"""
        pass
    
    def validate_client_side(self, field: EditableAttribute, value: Any) -> Dict[str, Any]:
        """Run client-side validation only"""
        return field.validate(self.validator, value, ValidationLevel.CLIENT)
    
class CliFormBuilder(FormBuilder):
    """CLI implementation of FormBuilder - primary input handler for CLI"""
    
    def render_form(self, form: EditableGroup) -> None:        
        self._render_group_recursive(form, level=0)
    
    def _render_group_recursive(self, group: EditableGroup, level: int = 0):
        """Recursively render group and children"""
        for child in group.children.values():
            if isinstance(child, EditableGroup):
                print(f"{'  ' * level}[{child.title}]")
                self._render_group_recursive(child, level + 1)
            elif isinstance(child, EditableAttribute):
                self._render_field_line(child, level)
    
    def _render_field_line(self, field: EditableAttribute, level: int = 0):
        """Render a single field line"""
        indent = "  " * level
        value_display = field.pending_value if field.pending_value is not None else "(empty)"
        
        print(f"{indent}{field.title}: {value_display}")
    
    def render_field(self, field: EditableAttribute) -> None:
        """Render a single field with full details"""
        # print(f"~ {field.title} ({field.input_type.__name__}) ~")
        # print(f"{field.description}")
        # if field.value:
        #     print(f"Current value: {field.value}")
    
    def get_user_input(self, field: EditableAttribute) -> Any:
        """Get user input for a field with client-side validation"""
        prompt = f"Enter value for {field.title}: " if not field.prompt else field.prompt
        prompt = "(required) " + prompt if field.required else prompt
                        
        while True:
            try:
                user_input = input(prompt)
                
                # Handle empty input for optional fields
                if not user_input and not field.required:
                    return field.value  # Keep existing value
                
                # Convert to appropriate type
                if field.input_type is bool:
                    user_input = user_input.lower() in ('true', 't', 'yes', 'y', '1')
                elif field.input_type in (int, float):
                    user_input = field.input_type(user_input)
                
                # Client-side validation
                validation_result = self.validate_client_side(field, user_input)
                if not validation_result["passed"]:
                    self.show_validation_error(field.name, validation_result["error"])
                    continue
                
                return user_input
                
            except (ValueError, TypeError) as e:
                self.logger.error(f"Invalid input: {e}")
                continue
            except KeyboardInterrupt:
                self.logger.warning("Input cancelled")
                return None
    
    def show_validation_error(self, field_name: str, error: Dict[str, Any]):
        """Display validation error to user"""
        message = error.get('message', 'Validation failed')
        self.logger.error(f"Error: {message}")
    
    def get_selection(self, prompt: str, options: List[str], default: Optional[str] = None) -> Optional[str]:
        """Get user selection from a list of options"""
        if not options:
            self.logger.error("No options provided for selection")
            return None

        # Display options
        print(f"{prompt}")
        print()
        for i, option in enumerate(options, 1):
            default_indicator = " (default)" if option == default else ""
            print(f"  {i}. {option}{default_indicator}")
        print()
        
        while True:
            try:
                choice = input("Select option (enter number or name): ").strip()
                
                # Handle empty input with default
                if not choice and default:
                    return default
                
                # Try to parse as number first
                try:
                    choice_num = int(choice)
                    if 1 <= choice_num <= len(options):
                        return options[choice_num - 1]
                    else:
                        self.logger.error(f"Number must be between 1 and {len(options)}")
                        continue
                except ValueError:
                    # Not a number, try exact match
                    if choice in options:
                        return choice
                    else:
                        self.logger.error(f"'{choice}' is not a valid option. Choose from: {', '.join(options)}")
                        continue
                        
            except KeyboardInterrupt:
                self.logger.warning("Selection cancelled")
                return None
    
    def confirm(self, message: str, default: bool = False) -> bool:
        """Get confirmation from user"""
        default_str = "y/N" if not default else "Y/n"
        response = input(f"{message} [{default_str}]: ").strip().lower()
        
        if not response:
            return default
            
        return response in ['y', 'yes']
    
    def fill_form_interactive(self, form: EditableGroup) -> bool:
        """Interactive form filling session"""
        # Set up handler registry for the form
        self.set_form_handler_registry(form)
        
        print(f"=== {form.title} ===")
        print()
        
        success = self._fill_group_recursive(form)
        
        if success:
            return self._handle_form_submission(form)
        else:
            self.logger.info("Form cancelled", "info")
            return False
    
    def _fill_group_recursive(self, group: EditableGroup, path: str = "") -> bool:
        """Recursively fill form fields"""
        for child_name, child in group.children.items():
            current_path = f"{path}.{child_name}" if path else child_name
            
            if isinstance(child, EditableGroup):
                print(f"--- {child.title} ---")
                if not self._fill_group_recursive(child, current_path):
                    return False
            elif isinstance(child, EditableAttribute):
                if not self._fill_field_interactive(child):
                    return False
        return True
    
    def _fill_field_interactive(self, field: EditableAttribute) -> bool:
        """Fill a single field interactively"""
        self.render_field(field)
        
        new_value = self.get_user_input(field)
        if new_value is None:  # User cancelled
            return False
        
        # Set the value
        try:
            field.value = new_value
            print("✓ Value set")
            print()
            return True
        except ValueError as e:
            self.logger.error(f"Failed to set value: {e}")
            return self._fill_field_interactive(field)  # Retry
    
    def _handle_form_submission(self, form: EditableGroup) -> bool:
        """Handle form submission"""
        print("=== Summary ===")
        
        self.render_form(form)
        
        if not self.confirm("\nSubmit form?"):
            self.logger.warning("Submission cancelled")
            return False
        
        # Validate entire form (server-side rules)
        validation_result = form.validate_all(self.validator, ValidationLevel.SERVER)
        if not validation_result["passed"]:
            self.logger.error("Validation errors:")
            self._print_validation_errors(validation_result["errors"])
            return False

        # Invoke handlers
        self.logger.info("Invoking handlers...")
        handler_results = self._invoke_form_handlers(form)
                
        if handler_results:
            self.logger.info("Form submitted successfully!")
            self._display_handler_results(handler_results)
        else:
            self.logger.info("Form submitted successfully! (No handlers to invoke)")

        # Commit all values
        if not form.commit_all_values(self.validator):
            self.logger.error("Failed to save form")
            return False
        
        return True
    
    def _invoke_form_handlers(self, form: EditableGroup) -> Dict[str, List[Any]]:
        """Invoke all handlers in the form"""
        results = {}
        
        def invoke_recursive(element, path: str = ""):
            current_path = f"{path}.{element.name}" if path else element.name
            
            if element.system_handler or element.user_defined_handler:
                try:
                    handler_results = element.invoke_handler()
                    if handler_results:
                        results[current_path] = handler_results
                except Exception as e:
                    results[current_path] = [{"type": "error", "error": str(e)}]
            
            if isinstance(element, EditableGroup):
                for child in element.children.values():
                    invoke_recursive(child, current_path)
        
        invoke_recursive(form)
        return results
    
    def _display_handler_results(self, results: Dict[str, List[Any]]):
        """Display handler execution results"""
        for path, handler_results in results.items():
            self.logger.info(f"\nHandler results for {path}:")
            for result in handler_results:
                result_type = result.get("type", "unknown")
                handler_name = result.get("handler", "unknown")
                if "error" in result:
                    self.logger.error(f"  {result_type} ({handler_name}): {result['error']}")
                elif "result" in result:
                    self.logger.info(f"  {result_type} ({handler_name}): {result['result']}")
    
    def _print_validation_errors(self, errors: Dict[str, Any], prefix: str = ""):
        """Print validation errors recursively"""
        for field_name, error in errors.items():
            field_path = f"{prefix}.{field_name}" if prefix else field_name
            
            if isinstance(error, dict) and "message" in error:
                self.logger.error(f"  {field_path}: {error['message']}")
            elif isinstance(error, dict):
                self._print_validation_errors(error, field_path)
            else:
                self.logger.error(f"  {field_path}: {error}")