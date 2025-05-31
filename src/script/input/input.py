import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Type, Union

from src.script.common.enums import CommandType, EntityType, HandlerType
from src.script.common.results import HandlerResult
from src.script.entity._base import EntityRef
from src.script.input.validation import (
    InputValidator,
    ValidationLevel,
    ValidationResult,
    ValidationRule,
)
from src.script.registry._base import Registry

 ######                                ##     ######                                ##                         ##
   ##                                  ##     ##   ##
   ##     ## ###   ######   ##   ##  ######   ##   ##   #####   ## ###   ### ##   ####      #####    #####   ####      #####   ## ###    #####
   ##     ###  ##  ##   ##  ##   ##    ##     ######   ##   ##  ###      ## # ##    ##     ##       ##         ##     ##   ##  ###  ##  ##
   ##     ##   ##  ##   ##  ##   ##    ##     ##       #######  ##       ## # ##    ##      ####     ####      ##     ##   ##  ##   ##   ####
   ##     ##   ##  ##   ##  ##  ###    ##     ##       ##       ##       ## # ##    ##         ##       ##     ##     ##   ##  ##   ##      ##
 ######   ##   ##  ######    ### ##     ###   ##        #####   ##       ##   ##  ######   #####    #####    ######    #####   ##   ##  #####
                   ##

class InputPermissions:
    """Permissions for Input modifications"""
    def __init__(self,
                 can_add_fields: bool = False,
                 can_remove_fields: bool = False,
                 can_modify_structure: bool = False,
                 can_set_user_handler: bool = False):
        self.can_add_fields = can_add_fields
        self.can_remove_fields = can_remove_fields
        self.can_modify_structure = can_modify_structure
        self.can_set_user_handler = can_set_user_handler
    
    def to_dict(self) -> Dict[str, bool]:
        return {
            "can_add_fields": self.can_add_fields,
            "can_remove_fields": self.can_remove_fields,
            "can_modify_structure": self.can_modify_structure,
            "can_set_user_handler": self.can_set_user_handler
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, bool]) -> 'InputPermissions':
        return cls(**data)    

 ######                                ##     ##   ##                ##
   ##                                  ##     ###  ##                ##
   ##     ## ###   ######   ##   ##  ######   ###  ##   #####    ######   #####
   ##     ###  ##  ##   ##  ##   ##    ##     ## # ##  ##   ##  ##   ##  ##   ##
   ##     ##   ##  ##   ##  ##   ##    ##     ## # ##  ##   ##  ##   ##  #######
   ##     ##   ##  ##   ##  ##  ###    ##     ##  ###  ##   ##  ##   ##  ##
 ######   ##   ##  ######    ### ##     ###   ##   ##   #####    ######   #####
                   ##

class InputNode(ABC):
    def __init__(self,
                 name: str,
                 title: str): 

        self.name = name
        self.title = title
        self.parent = None

        self.logger = logging.getLogger(f"{self.__class__.__name__}")

    @property
    def level(self):
        return self.parent.level+1 if self.parent else 0

    @property
    def root_parent(self):
        return self.parent.root_parent if self.parent else self

    @property
    def permissions(self):
        return self.parent._permissions if self.parent else InputPermissions()

    @permissions.setter
    def permissions(self, val):
        self._permissions = val

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def load_from_dict(self, data: Dict[str, bool]) -> Dict[str, Any]:
        pass

 ######                                ##     #######    ##               ###          ##
   ##                                  ##     ##                           ##          ##
   ##     ## ###   ######   ##   ##  ######   ##       ####      #####     ##      ######
   ##     ###  ##  ##   ##  ##   ##    ##     #####      ##     ##   ##    ##     ##   ##
   ##     ##   ##  ##   ##  ##   ##    ##     ##         ##     #######    ##     ##   ##
   ##     ##   ##  ##   ##  ##  ###    ##     ##         ##     ##         ##     ##   ##
 ######   ##   ##  ######    ### ##     ###   ##       ######    #####    ####     ######
                   ##

class InputField(InputNode):
    """Unified input field - can be used as spec or resolved input"""
    def __init__(self,
                 field_type: Type[Any] = str,
                 required: bool = False,
                 default_value: Any = None,
                 description: Optional[str] = None,
                 choices: Optional[Union[List[Any], Dict[str, Any], Callable]] = None,
                 allow_multiple: Optional[bool] = False,
                 validation_rules: Optional[Union[List[ValidationRule], Callable]] = None,
                 # UI hints
                 prompt: Optional[str] = None,
                 placeholder: Optional[str] = None,
                 help_text: Optional[str] = None,
                 widget_type: Optional[str] = None,
                 # Command hints  
                 short_name: Optional[str] = None,
                 param_type: str = "named",
                 # Dynamic behavior
                 hidden: bool = False,
                 **kwargs):
        super().__init__(**kwargs)
        
        self.field_type = field_type
        self.required = required
        self.default_value = default_value
        self.description = description
        self.choices = choices
        self.allow_multiple = allow_multiple
        self.validation_rules = validation_rules or []
        
        # UI hints
        self.prompt = prompt
        self.placeholder = placeholder
        self.help_text = help_text
        self.widget_type = widget_type
        
        # Command hints
        self.short_name = short_name
        self.param_type = param_type
        
        # Dynamic behavior
        self.hidden = hidden
        
        # Runtime state
        self._value = None
        self._pending_value = None
        self._is_pending = False
    
    @property
    def value(self) -> Any:
        return self._value
    
    @value.setter
    def value(self, val: Any):
        self._is_pending = True
        self._pending_value = val
    
    @property
    def pending_value(self) -> Any:
        return self._pending_value
    
    @property
    def is_pending(self) -> bool:
        return self._is_pending
    
    def get_choice_display_names(self) -> List[str]:
        """Get display names for choices (handles both list and dict formats)"""
        if not self.choices:
            return []
        
        choices = self.choices
        if callable(choices):
            try:
                choices = choices()
            except:
                return []
        
        if isinstance(choices, dict):
            return list(choices.keys())
        elif isinstance(choices, list):
            return [str(choice) for choice in choices]
        else:
            return []
    
    def get_choice_value(self, display_name: str) -> Any:
        """Get the actual value for a choice display name"""
        if not self.choices:
            return display_name
        
        choices = self.choices
        if callable(choices):
            try:
                choices = choices()
            except:
                return display_name
        
        if isinstance(choices, dict):
            return choices.get(display_name, display_name)
        else:
            # For lists, the display name is the value
            return display_name

    def compute_dynamic_value(self, field_values: Dict[str, Any] = None) -> Any:
        """Compute dynamic value if default_value is callable"""
        if callable(self.default_value):
            try:
                if field_values is None:
                    field_values = self._get_sibling_field_values()
                
                computed_value = self.default_value(field_values)
                return computed_value
            except Exception as e:
                self.logger.error(f"Error computing dynamic value for {self.name}: {e}")
                return None
        else:
            return self.default_value

    def _get_sibling_field_values(self) -> Dict[str, Any]:
        """Get values of all sibling fields in the same group"""
        if not self.parent:
            return {}
        
        values = {}
        
        def collect_values(node):
            if isinstance(node, InputField) and node.name != self.name:
                # Use pending value if available, otherwise current value
                value = node.pending_value if node.is_pending else node.value
                values[node.name] = value
            elif isinstance(node, InputGroup):
                for child in node.children.values():
                    collect_values(child)
        
        # Collect from parent group
        for sibling in self.parent.children.values():
            collect_values(sibling)
        
        return values

    def commit_value(self) -> bool:
        """Commit pending value to actual value"""
        
        if not self._is_pending:
            return True
        
        try:
            # Validate before commit - now returns ValidationResult
            validation_result = self.validate(self._pending_value)
            if validation_result.is_failure:  # Changed from not validation_result["passed"]
                return False
            
            # Commit the value
            self._value = self._pending_value
            self._pending_value = None
            self._is_pending = False
            return True
            
        except Exception:
            return False

    # Replace the existing validate method in InputField class:
    def validate(self, value: Any = None) -> ValidationResult:
        """Validate a value"""
        if value is not None:
            test_value = value
        elif self.is_pending:
            test_value = self._pending_value  # This is the fix!
        else:
            test_value = self._value

        complete_rules = self._setup_validation_rules()

        result = InputValidator.validate(test_value, complete_rules)
        
        # Update field names in errors (since ValidationRule doesn't know the field name)
        if result.is_failure:
            updated_field_errors = {}
            updated_errors = []
            
            for error in result._errors:
                error.field = self.name  # Set the correct field name
                updated_errors.append(error)
            
            updated_field_errors[self.name] = updated_errors
            
            new_result = ValidationResult()
            new_result.field_errors = updated_field_errors
            new_result._errors = updated_errors
            new_result._value = False
            return new_result
        
        return result

    def _setup_validation_rules(self) -> List[ValidationRule]:
        """Set up complete validation rules including required and type checking"""
        rules = []
        
        # Required field validation
        if self.required:
            rules.append(InputValidator.input_provided(ValidationLevel.CLIENT))
        
        # Type validation
        if self.field_type:
            rules.append(InputValidator.is_type(self.field_type, ValidationLevel.CLIENT))
        
        # Add custom validation rules
        if isinstance(self.validation_rules, list):
            rules.extend(self.validation_rules)
        
        return rules

    def to_dict(self) -> Dict[str, Any]:
        """Serialize field to dictionary - only stores the value"""
        return {
            "name": self.name,
            "value": self._value
        }

    def load_from_dict(self, data: Dict[str, Any]):
        """Load field value from dictionary"""
        if "value" in data:
            try:
                # Set the value directly (not pending)
                self._value = data["value"]
                self._pending_value = None
                self._is_pending = False
            except (ValueError, TypeError) as e:
                self.logger.error(f"Failed to load value for field {self.name}: {e}")

 ######                                ##       ####
   ##                                  ##      ##  ##
   ##     ## ###   ######   ##   ##  ######   ##       ## ###    #####   ##   ##  ######
   ##     ###  ##  ##   ##  ##   ##    ##     ##       ###      ##   ##  ##   ##  ##   ##
   ##     ##   ##  ##   ##  ##   ##    ##     ##  ###  ##       ##   ##  ##   ##  ##   ##
   ##     ##   ##  ##   ##  ##  ###    ##      ##  ##  ##       ##   ##  ##  ###  ##   ##
 ######   ##   ##  ######    ### ##     ###     #####  ##        #####    ### ##  ######
                   ##                                                             ##

class InputGroup(InputNode):
    """Unified input group - can be used as spec or resolved input"""
    def __init__(self,
                 children: List[Union[InputField, 'InputGroup']],
                 description: Optional[str] = None,
                 **kwargs):

        super().__init__(**kwargs)
        self.description = description
        
        # Set up children
        self._children: Dict[str, Union[InputField, 'InputGroup']] = {}
        for child in children:
            self._children[child.name] = child
            child.parent = self
        
    @property
    def children(self) -> Dict[str, Union[InputField, 'InputGroup']]:
        return self._children.copy()

    def append_child(self, child: InputNode):
        if self._permissions.can_add_fields:
            self._children = self._children | {child.name : child }
        else:
            self.logger.warning("Can't add children")

    def prepend_child(self, child: InputNode):
        if self._permissions.can_add_fields:
            self._children =  {child.name : child } | self._children
        else:
            self.logger.warning("Can't add children")

    def remove_child(self, child: InputNode):
        if self._permissions.can_remove_fields:
            if child in self._children:
                del self._children[child.name]
            else:
                self.logger.error("Child not present in input children")
        else:
            self.logger.warning("Can't add children")
    
    def validate_all(self) -> ValidationResult:
        """Validate all children"""
        
        combined_result = ValidationResult.success()
        
        for name, child in self._children.items():
            if isinstance(child, InputField):
                result = child.validate()
                if result.is_failure:
                    combined_result.field_errors.update(result.field_errors)
                    combined_result._errors.extend(result._errors)
                    combined_result._value = False
            elif isinstance(child, InputGroup):
                result = child.validate_all()
                if result.is_failure:
                    combined_result.field_errors.update(result.field_errors)
                    combined_result._errors.extend(result._errors)
                    combined_result._value = False
        
        return combined_result
        
    def commit_all_values(self) -> bool:
        """Commit all pending values in children"""
        
        success = True
        for child in self._children.values():
            if isinstance(child, InputField):
                if not child.commit_value():
                    success = False
            elif isinstance(child, InputGroup):
                if not child.commit_all_values():
                    success = False
        return success

    def to_dict(self) -> Dict[str, Any]:
        """Serialize group to dictionary - only stores children values"""
        return {
            "name": self.name,
            "children": {name: child.to_dict() for name, child in self._children.items()}
        }

    def load_from_dict(self, data: Dict[str, Any]):
        """Load group values from dictionary"""
        children_data = data.get("children", {})
        for name, child in self._children.items():
            if name in children_data:
                child.load_from_dict(children_data[name])

 ######                                ##
   ##                                  ##
   ##     ## ###   ######   ##   ##  ######
   ##     ###  ##  ##   ##  ##   ##    ##
   ##     ##   ##  ##   ##  ##   ##    ##
   ##     ##   ##  ##   ##  ##  ###    ##
 ######   ##   ##  ######    ### ##     ###
                   ##

class Input(InputGroup):
    """Main input container"""
    def __init__(self,
                 handler_registry: Registry,
                 entity_type: Optional[EntityType] = None,
                 command_type: Optional[CommandType] = None,
                 requires_auth: bool = True,
                 confirm_submit: bool = True,
                 on_submit: Optional[Callable[[Dict[str, Any]], None]] = None,
                 idempotent: bool = False,
                 permissions: Optional[InputPermissions] = None,
                 **kwargs):
        
        super().__init__(**kwargs)
        
        # Specification metadata
        self.entity_type = entity_type
        self.command_type = command_type
        self.requires_auth = requires_auth
        self.confirm_submit = confirm_submit
        self.on_submit = on_submit
        self.idempotent = idempotent
        self._permissions = permissions or InputPermissions()
        
        # Handler support
        self._system_handler_ref = None
        self._handler_registry = handler_registry
        self._handler_refs = []

    def add_system_handler(self, handler_ref: EntityRef):
        self._system_handler_ref = handler_ref
        self.add_handler(handler_ref)

    def add_handler(self, handler_ref: EntityRef) -> Dict:
        
        handler = self._handler_registry.get_by_ref(handler_ref)

        if handler.handler_type is HandlerType.USER and self.permissions.can_set_user_handler is False:
            self.logger.warning("Not allowed to add handlers to input")
            return {'success': False, 'code': 'Not permitted to add handlers to this Input'}
        else:
            self._handler_refs.append(handler_ref)
            return {'success': True, 'code': ''}

    @property
    def handler_registry(self):
        return self._handler_registry

    @property
    def system_handler_ref(self):
        return self._system_handler_ref
    
    @property
    def handler_refs(self) -> Optional[str]:
        return self._handler_refs
    
    @handler_refs.setter
    def handler_refs(self, refs: List[EntityRef]):
        self._handler_refs = refs

    def invoke_handlers(self, context, **kwargs) -> HandlerResult:
        """Invoke both system-defined and user-defined handlers"""

        results = []

        kwargs['context'] = context

        if self._handler_registry:
            for handler_ref in self._handler_refs:
                try:
                    handler = self._handler_registry.get_by_ref(handler_ref)
                    result = handler(**kwargs)
                    handler_result = HandlerResult.success(
                        value=result,
                        handler=handler,
                    )
                except Exception as e:
                    handler_result = HandlerResult.failure(
                        message=str(e),
                        handler=handler
                    )

            results.append(handler_result)

        return results