# _input_converter.py - Updated without mutually exclusive group handling

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from src.script.input.input import Input, InputField, InputGroup


class ApiInputConverter(ABC):
    """Abstract base class for converting inputs to API-specific formats"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
    
    @abstractmethod
    def to_api_spec(self, input_obj: Input) -> Dict[str, Any]:
        """Convert input object to API-specific specification format"""
        pass
    
    @abstractmethod
    def collect_missing_inputs(self, input_obj: Input, provided_inputs: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Collect missing inputs in an API-appropriate way"""
        pass
    
    @abstractmethod
    def display_structure(self, input_obj: Input, context: Dict[str, Any] = None) -> Any:
        """Display the input structure in an API-appropriate way"""
        pass
    
    def execute_with_input_collection(self, input_obj: Input, command_type: str, provided_inputs: Dict[str, Any] = None, context: Dict[str, Any] = None) -> Any:
        """Execute command with automatic missing input collection"""
        
        provided_inputs = provided_inputs or {}
        context = context or {}
        
        # Check for missing inputs and collect if needed
        missing = self.check_missing_inputs(input_obj, provided_inputs)
        
        if missing:
            input_result = self.collect_missing_inputs(input_obj, provided_inputs, context)
            if input_result.get("success"):
                provided_inputs.update(input_result.get("inputs", {}))
            else:
                return input_result
        
        # Apply inputs to fields (this sets pending values and computes dynamic values)
        self._apply_inputs_to_input(input_obj, provided_inputs, context)

        # Validate pending values
        validation_result = self._validate_all_pending_values(input_obj, context)
        if not validation_result["passed"]:
            return {"success": False, "validation_errors": validation_result["errors"]}
        
        # Commit values only after validation passes
        if not input_obj.commit_all_values():
            return {"success": False, "error": "Failed to commit values"}
        
        # Execute handler - now using the enhanced result structure
        values = self._extract_field_values_from_input(input_obj)
        
        # Call the handler through the input object
        handler_result = input_obj.invoke_handlers(context=context, **values)
        
        # Return the simplified result structure
        return {"success": True, "result": handler_result}

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
                    if node.name not in provided_inputs or provided_inputs[node.name] is None:
                        missing.append(node.name)
            
            elif isinstance(node, InputGroup):  # Group-like (including Input)
                # Recursively check children
                for child in node.children.values():
                    check_node(child)
        
        check_node(input_obj)
        return missing
    
    def _validate_all_pending_values(self, input_obj, context) -> Dict[str, Any]:
        """Validate all pending values in the input structure"""
        results = {"passed": True, "errors": {}}
        
        def validate_node(node):
            if isinstance(node, InputField):  # Field-like
                # Validate the pending value if it exists, otherwise the current value
                value_to_validate = node.pending_value if node.is_pending else node.value
                result = node.validate(value_to_validate)
                if not result["passed"]:
                    results["passed"] = False
                    results["errors"][node.name] = result["error"]
            elif isinstance(node, InputGroup):  # Group-like
                # Recursively validate children
                for child in node.children.values():
                    validate_node(child)
        
        validate_node(input_obj)
        return results

    def _apply_inputs_to_input(self, input_obj, inputs: Dict[str, Any], context: Dict[str, Any] = None):
        """Apply input values to fields in input and compute dynamic values"""
        context = context or {}
        
        def apply_to_node(node):
            if isinstance(node, InputField):  # Field-like
                # First, compute dynamic value if needed
                if getattr(node, 'hidden', False) or callable(node.default_value):
                    # Get current field values for dynamic computation
                    field_values = self._extract_current_field_values_from_group(node.parent or input_obj)
                    # Include provided inputs in the field values
                    field_values.update(inputs)
                    
                    dynamic_value = node.compute_dynamic_value(field_values)
                    if dynamic_value is not None:
                        node.value = dynamic_value
                
                # Apply provided input value (this may override dynamic value for non-hidden fields)
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
        
        apply_to_node(input_obj)

    def _extract_current_field_values_from_group(self, group) -> Dict[str, Any]:
        """Extract current field values from a group (for dynamic computation)"""
        values = {}
        
        def extract_from_node(node):
            if isinstance(node, InputField):
                # Use pending value if available, otherwise current value
                value = node.pending_value if node.is_pending else node.value
                values[node.name] = value
            elif isinstance(node, InputGroup):
                for child in node.children.values():
                    extract_from_node(child)
        
        if group:
            extract_from_node(group)
        
        return values

    def _extract_field_values_from_input(self, input_obj) -> Dict[str, Any]:
        """Extract all field values from input"""
        params = {}
        
        if isinstance(input_obj, InputField):  # Field-like
            params[input_obj.name] = input_obj.value
        elif isinstance(input_obj, InputGroup):  # Group-like (including Input)
            for child in input_obj.children.values():
                child_params = self._extract_field_values_from_input(child)
                params.update(child_params)
        
        return params