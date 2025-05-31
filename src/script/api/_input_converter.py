# _input_converter.py - Updated without mutually exclusive group handling

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from src.script.common.results import ApiResult, ValidationResult
from src.script.input.input import Input, InputField, InputGroup


class ApiInputConverter(ABC):
    """Abstract base class for converting inputs to API-specific formats"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
    
    @abstractmethod
    def to_api_spec(self, input_obj: Input) -> Dict[str, Any]:
        """Convert input object to API-specific format so that it can be interacted with by the user through the API presentation layer"""
        pass
    
    # Replace the abstract method signature in ApiInputConverter:
    @abstractmethod
    def collect_inputs(self, input_obj: Input, provided_inputs: Dict[str, Any], context: Dict[str, Any] = None) -> ApiResult:
        """Collect missing inputs in an API-appropriate way"""
        pass
    
    def execute_with_input_collection(self, input_obj: Input, command_type: str, provided_inputs: Dict[str, Any] = None, context: Dict[str, Any] = None) -> Any:
        """Execute command with automatic missing input collection"""
        
        provided_inputs = provided_inputs or {}
        context = context or {}
        
        # Check for missing inputs and collect if needed
        missing = self.check_missing_inputs(input_obj, provided_inputs)
        
        if missing:
            input_result = self.collect_inputs(input_obj, provided_inputs, context)  # Now returns Result
            if input_result.is_failure:
                return input_result
            provided_inputs.update(input_result.value)
        
        # Apply inputs to fields (this sets pending values and computes dynamic values)
        try:
            self._apply_inputs_to_input(input_obj, provided_inputs, context)
        except Exception as e:
            return ApiResult.failure(
                message=f"Failed to apply inputs: {str(e)}")

        # Validate pending values
        validation_result = self._validate_all_pending_values(input_obj, context)
        if validation_result.is_failure:
            error_details = []
            for field, errors in validation_result.field_errors.items():
                for error in errors:
                    error_details.append(f"{field}: {error.message}")
            
            return ApiResult.failure(
                message=f"Validation failed: {'; '.join(error_details)}",
                code="validation_failed",
            )

        
        # Commit values only after validation passes
        try:
            if not input_obj.commit_all_values():
                return ApiResult.failure(
                    message="Failed to commit values",
                    code="commit_failed"
                )
        except Exception as e:
            return ApiResult.failure(message=f"Commit failed: {str(e)}")
            
        # Execute handler - now using the enhanced result structure
        try:
            values = self._extract_field_values_from_input(input_obj)
            handler_results = input_obj.invoke_handlers(context=context, **values)  # Returns List[HandlerResult]
            return ApiResult.success(handler_results)
        except Exception as e:
            return ApiResult.failure(message=f"Handler execution failed: {str(e)}")
            

    def check_missing_inputs(self, input_obj: Input, provided_inputs: Dict[str, Any]) -> List[str]:
        """Check which required inputs are missing - common implementation"""
        missing = []
        
        def check_node(node):
            
            if isinstance(node, InputField):  # Field-like
                
                # Skip hidden fields - they'll be auto-computed
                if getattr(node, 'hidden', False):
                    return
                
                if node.required:
                    # Check if the field has a value in provided_inputs
                    is_missing = node.name not in provided_inputs or provided_inputs[node.name] is None
                    if is_missing:
                        missing.append(node.name)
            
            elif isinstance(node, InputGroup):  # Group-like (including Input)
                # Recursively check children
                for child in node.children.values():
                    check_node(child)
        
        check_node(input_obj)
        return missing
    
    def _validate_all_pending_values(self, input_obj, context) -> ValidationResult:
        """Validate all pending values in the input structure"""
        combined_result = ValidationResult.success()
        
        def validate_node(node):
            if isinstance(node, InputField):
                # Validate the pending value if it exists, otherwise the current value
                value_to_validate = node.pending_value if node.is_pending else node.value
                
                result = node.validate(value_to_validate)
                
                if result.is_failure:
                    combined_result.field_errors.update(result.field_errors)
                    combined_result._errors.extend(result._errors)
                    combined_result._value = False
            elif isinstance(node, InputGroup):
                # Recursively validate children
                for child in node.children.values():
                    validate_node(child)
        
        validate_node(input_obj)
        return combined_result

    def _apply_inputs_to_input(self, input_obj, inputs: Dict[str, Any], context: Dict[str, Any] = None):
        """Apply input values to fields in input and compute dynamic values"""
        context = context or {}
        
        def apply_to_node(node):
            if isinstance(node, InputField):  # Field-like
                
                # Apply provided input value first (for non-hidden fields)
                if not getattr(node, 'hidden', False) and node.name in inputs:
                    
                    # Handle dict choices - convert display name to actual value
                    if hasattr(node, 'choices') and node.choices and isinstance(inputs[node.name], str):
                        actual_value = node.get_choice_value(inputs[node.name])
                        node.value = actual_value
                    else:
                        node.value = inputs[node.name]
                
            elif isinstance(node, InputGroup):  # Group-like (including Input)
                for child in node.children.values():
                    apply_to_node(child)
        
        # First pass: apply all provided inputs
        apply_to_node(input_obj)
        
        # Second pass: compute dynamic values for hidden fields or fields with callable defaults
        def compute_dynamic_values(node):
            if isinstance(node, InputField):
                # Compute dynamic value if needed (hidden fields or callable defaults)
                if getattr(node, 'hidden', False) or callable(node.default_value):
                    
                    # Get current field values for dynamic computation
                    field_values = self._extract_current_field_values_from_group(node.parent or input_obj)
                    # Include provided inputs in the field values
                    field_values.update(inputs)
                    
                    
                    dynamic_value = node.compute_dynamic_value(field_values)
                    
                    if dynamic_value is not None:
                        node.value = dynamic_value
                        
            elif isinstance(node, InputGroup):  # Group-like (including Input)
                for child in node.children.values():
                    compute_dynamic_values(child)
        
        # Second pass: compute dynamic values
        compute_dynamic_values(input_obj)

    def _extract_current_field_values_from_group(self, group) -> Dict[str, Any]:
        """Extract current field values from a group (for dynamic computation)"""
        values = {}
        
        def extract_from_node(node):
            if isinstance(node, InputField):
                # Use pending value if available, otherwise current value
                field_value = node.pending_value if node.is_pending else node.value
                values[node.name] = field_value
            elif isinstance(node, InputGroup):
                for child in node.children.values():
                    extract_from_node(child)
        
        if group:
            extract_from_node(group)
        
        return values

    def _extract_field_values_from_input(self, input_obj) -> Dict[str, Any]:
        """Extract all field values from input - including pending values"""
        params = {}
        
        def extract_from_node(node):
            if isinstance(node, InputField):  # Field-like
                # Use pending value if available, otherwise current value
                field_value = node.pending_value if node.is_pending else node.value
                params[node.name] = field_value
            elif isinstance(node, InputGroup):  # Group-like (including Input)
                for child in node.children.values():
                    extract_from_node(child)
        
        extract_from_node(input_obj)
        return params