# cli.py
from typing import Any, Dict

from src.script.api._input_converter import ApiInputConverter
from src.script.constants import CommandType


class RestInputConverter(ApiInputConverter):
    """REST-specific input converter"""
    
    def to_api_spec(self) -> Dict[str, Any]:
        """Convert to OpenAPI specification"""
        parameters = []
        
        def process_node(element):
            if hasattr(element, 'param_type'):  # Field-like
                param_spec = {
                    "name": element.name,
                    "in": "query" if getattr(element, 'param_type', 'named') == "named" else "path",
                    "required": element.required,
                    "type": element.field_type.__name__ if hasattr(element, 'field_type') else "string",
                    "description": getattr(element, 'description', None)
                }
                
                if hasattr(element, 'choices') and element.choices:
                    param_spec["enum"] = element.choices
                
                parameters.append(param_spec)
                
            elif hasattr(element, 'children'):  # Container-like
                for child in element.children.values():
                    process_node(child)
        
        process_node(self)
        
        # Determine HTTP method
        method_map = {
            CommandType.CREATE: "POST",
            CommandType.LIST: "GET",
            CommandType.DELETE: "DELETE",
            CommandType.UPDATE: "PUT",
            CommandType.DETAIL: "GET",
            CommandType.RENAME: "PUT"
        }
        
        command_type = getattr(self, 'command_type', None)
        entity_type = getattr(self, 'entity_type', 'resource')
        
        return {
            "path": f"/{entity_type}/{self.name}",
            "method": method_map.get(command_type, "POST"),
            "parameters": parameters,
            "description": getattr(self, 'description', None)
        }
    
    def collect_missing_inputs(self, provided_inputs: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """For REST, return missing fields for client-side handling"""
        missing = self.check_missing_inputs(provided_inputs)
        
        if missing:
            return {
                "success": False,
                "missing_fields": missing,
                "message": "Missing required fields"
            }
        
        return {"success": True, "inputs": provided_inputs}
    
    def display_structure(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Return JSON schema for REST API documentation"""
        schema = {"type": "object", "properties": {}, "required": []}
        
        def process_node(node, schema_obj):
            if hasattr(node, 'value_type'):  # Field-like
                prop_schema = {
                    "type": self._get_json_type(node.field_type),
                    "title": node.title,
                    "description": getattr(node, 'description', None)
                }
                
                if hasattr(node, 'choices') and node.choices:
                    prop_schema["enum"] = node.choices
                
                if hasattr(node, 'default_value') and node.default_value is not None:
                    prop_schema["default"] = node.default_value
                
                schema_obj["properties"][node.name] = prop_schema
                
                if node.required:
                    schema_obj["required"].append(node.name)
                    
            elif hasattr(node, 'children'):  # Container-like
                for child in node.children.values():
                    process_node(child, schema_obj)
        
        process_node(self, schema)
        return schema
    
    def _get_json_type(self, python_type):
        """Convert Python type to JSON schema type"""
        type_map = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object"
        }
        return type_map.get(python_type, "string")
