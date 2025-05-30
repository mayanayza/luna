# Enhanced api.py - Clear command lifecycle with streamlined debug logging

import time
from abc import abstractmethod
from typing import Any, Dict, List, Union

from src.script.api._enum import CommandType
from src.script.common.decorators import classproperty
from src.script.entity._entity import ListableEntity
from src.script.entity._enum import EntityType
from src.script.input.factory import InputFactory
from src.script.input.input import Input, InputPermissions


class Api(ListableEntity):
    """Base API class with clear command lifecycle"""
    
    def __init__(self, registry, **kwargs):
        super().__init__(registry, **kwargs)
    
    @classproperty
    def type(self):
        return EntityType.API

    @property
    @abstractmethod
    def input_converter(self):
        """Subclasses must implement their specific input converter"""
        pass

    @property
    @abstractmethod
    def user_interface(self):
        """Subclasses must implement their specific user interface"""
        pass
    
    @abstractmethod
    def start(self):
        """Start the API with the provided application context."""
        pass

    def execute_command(self, 
                       entity_type: Union[EntityType, str], 
                       command_type: Union[CommandType, str], 
                       **params) -> Dict[str, Any]:
        """
        Execute a command - main entry point for all API types
        
        Args:
            entity_type: EntityType enum or string
            command_type: CommandType enum or string  
            **params: Command parameters
            
        Returns:
            Dict with success status and results
        """
        start_time = time.time()
        
        try:
            # Normalize to enums if strings provided
            if isinstance(entity_type, str):
                entity_type = EntityType(entity_type)
            if isinstance(command_type, str):
                command_type = CommandType(command_type)

            self.logger.info(f"Executing {command_type.value} on {entity_type.value} with params: {params}")
            
            # 1. Prepare command - find handlers and input object
            prep_start = time.time()
            input_obj = self._prepare_command(entity_type, command_type)
            prep_time = time.time() - prep_start
            self.logger.debug(f"Command preparation: {prep_time:.3f}s")
            
            # 2. Collect inputs - convert and gather missing inputs, submit inputs
            collect_start = time.time()
            collected_inputs = self._collect_inputs(input_obj, params)
            collect_time = time.time() - collect_start
            self.logger.debug(f"Input collection: {collect_time:.3f}s")
            
            self.logger.debug(f"Collected inputs: {collected_inputs}")

            if not collected_inputs.get("success"):
                self.logger.error(f"Input collection failed: {collected_inputs.get('error', 'Unknown error')}")
                return collected_inputs
            
            # 3. Execute handlers with collected inputs
            exec_start = time.time()
            handler_results = self._execute_handlers(input_obj, collected_inputs["inputs"])
            exec_time = time.time() - exec_start
            self.logger.debug(f"Handler execution: {exec_time:.3f}s")
            
            # 4. Process results and handle callbacks
            process_start = time.time()
            final_result = self._process_results(handler_results, command_type, input_obj, collected_inputs["inputs"])
            process_time = time.time() - process_start
            self.logger.debug(f"Result processing: {process_time:.3f}s")
            
            total_time = time.time() - start_time
            self.logger.info(f"Command completed successfully in {total_time:.3f}s")
            
            return final_result
            
        except Exception as e:
            total_time = time.time() - start_time
            self.logger.error(f"Command failed after {total_time:.3f}s: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    def _prepare_command(self, 
                        entity_type: EntityType, 
                        command_type: CommandType) -> tuple[List, Input]:
        """
        Prepare command for execution - find handlers and prepare input object
        
        Args:
            entity_type: The entity type enum
            command_type: The command type enum
            
        Returns:
            Tuple of (handlers_list, input_object)
        """
        # Find the handlers
        system_handler = self.handler_registry.get_system_handler_for_entity_and_command_type(
            entity_type, command_type
        )
        
        if not system_handler:
            raise ValueError(f"No system handler found for {entity_type.value}.{command_type.value}")

        self.logger.debug(f"Found system handler: {system_handler.ref} (needs_target: {system_handler.needs_target})")

        input_obj = system_handler.input_obj

        all_handlers = self.handler_registry.get_handlers_by_entity_and_command_types(
            entity_type, command_type
        )
        
        self.logger.debug(f"Found {len(all_handlers)} handlers: {[h.ref for h in all_handlers]}")
        
        for handler in all_handlers:
            input_obj.add_handler(handler.ref)

        # For entity-specific commands, add target selector if needed
        if system_handler.needs_target:
            input_obj = self._add_target_selector(input_obj, system_handler)
            self.logger.debug("Added target selector to input object")

        return input_obj

    def _add_target_selector(self, input_obj: Input, handler) -> Input:
        """Add entity target selector to input if needed"""
        # Temporarily allow field addition
        original_permissions = input_obj.permissions.to_dict()
        temp_permissions = original_permissions.copy()
        temp_permissions['can_add_fields'] = True
        input_obj.permissions = InputPermissions.from_dict(temp_permissions)
        
        # Get entity selector configuration from handler
        selector_config = handler.get_entity_selector_config()
        entity_type = handler.entity_type
        param_name = handler.get_entity_param_name()

        # Create entity selector field with handler-specific configuration
        registry = input_obj.handler_registry.manager.get_by_entity_type(entity_type)
        entity_selector_field = InputFactory.entity_target_selector_field(
            name=param_name,
            registry=registry,
            **selector_config
        )

        input_obj.prepend_child(entity_selector_field)
        
        # Restore original permissions
        input_obj.permissions = InputPermissions.from_dict(original_permissions)
        
        return input_obj

    def _collect_inputs(self, 
                       input_obj: Input, 
                       provided_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Collect and validate inputs using the converter
        
        Args:
            input_obj: The input specification
            provided_params: Parameters already provided
            
        Returns:
            Dict with success status and collected inputs
        """
        context = {"api_type": self.name}
        
        try:
            result = self.input_converter.collect_inputs(input_obj, provided_params, context=context)
            
            if result.get("success"):
                collected = result.get("inputs", {})
                self.logger.debug(f"Collected inputs: {list(collected.keys())}")
            else:
                self.logger.error(f"Input collection failed: {result.get('error', 'Unknown error')}")
                
            return result
            
        except Exception as e:
            self.logger.error(f"Exception during input collection: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Input collection failed: {str(e)}"
            }

    def _execute_handlers(self, 
                         input_obj: Input, 
                         collected_inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute all handlers with the collected inputs
        
        Args:
            input_obj: The input object (contains handler references)
            collected_inputs: All collected and validated inputs
            
        Returns:
            Dict of handler results keyed by handler.ref
        """
        handler_count = len(input_obj.handlers) if hasattr(input_obj, 'handlers') else 0
        self.logger.debug(f"Executing {handler_count} handlers with inputs: {list(collected_inputs.keys())}")
        
        try:
            context = {"api_type": self.__class__.__name__.lower()}
            handler_results = input_obj.invoke_handlers(context, **collected_inputs)
            
            # Log handler execution results
            if isinstance(handler_results, list):
                success_count = sum(1 for r in handler_results if hasattr(r, 'success') and r.success)
                self.logger.debug(f"Handler results: {success_count}/{len(handler_results)} successful")
                
                for result in handler_results:
                    if hasattr(result, 'success') and not result.success:
                        handler_ref = getattr(result, 'handler_ref', 'unknown')
                        error = getattr(result, 'error', 'Unknown error')
                        self.logger.warning(f"Handler {handler_ref} failed: {error}")
            
            return handler_results
            
        except Exception as e:
            self.logger.error(f"Handler execution failed: {e}", exc_info=True)
            return {
                "error": f"Handler execution failed: {str(e)}"
            }

    def _process_results(self, 
                        handler_results: Dict[str, Any], 
                        command_type: CommandType,
                        input_obj: Input,
                        collected_inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process handler results and execute callbacks
        
        Args:
            handler_results: Results from handler execution
            command_type: Command type for logging/display
            input_obj: Input object (for callback access)
            collected_inputs: The inputs that were used
            
        Returns:
            Final processed result dictionary
        """
        if hasattr(handler_results, 'error'):
            self.logger.error(f"Handler results contain error: {handler_results.error}")
            return {
                "success": False,
                "error": f"Handler execution failed: {handler_results.error}"
            }

        try:                        
            # Process each handler result
            successful_results = []
            for i, handler_result in enumerate(handler_results):
                if hasattr(handler_result, 'success') and handler_result.success:
                    successful_results.append(handler_result)
                    
                    # Display results for successful handlers
                    if hasattr(handler_result, 'result'):
                        self.display_results(command_type, handler_result.result)
                else:
                    # Handler execution failed
                    handler_ref = getattr(handler_result, 'handler_ref', f"handler_{i+1}")
                    error_info = getattr(handler_result, 'error', "Unknown error")
                    
                    self.logger.error(f"Handler {handler_ref} failed: {error_info}")
                    error_msg = f"Handler {handler_ref} failed: {error_info.get('error', 'Unknown error') if isinstance(error_info, dict) else error_info}"
                    
                    return {
                        "success": False,
                        "error": error_msg,
                        "handler_error": error_info
                    }

            # Execute on_submit callback if present
            if hasattr(input_obj, 'on_submit') and input_obj.on_submit:
                try:
                    self.logger.debug("Executing on_submit callback")
                    callback_result = {
                        "success": True,
                        "results": successful_results,
                        "inputs": collected_inputs,
                        "internal_api": self.registry.manager.get_by_entity_type(EntityType.API).get_by_name('internal')
                    }
                    
                    input_obj.on_submit(**callback_result)
                    
                except Exception as e:
                    # Log callback errors but don't fail the main operation
                    self.logger.error(f"On-submit callback failed: {e}", exc_info=True)

            return {
                "success": True,
                "results": successful_results
            }
            
        except Exception as e:
            self.logger.error(f"Result processing failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Result processing failed: {str(e)}"
            }
    
    def display_results(self, command_type: CommandType, results: Any) -> None:
        """Display command results appropriately based on command type"""
        if not results:
            self.user_interface.respond("No results returned")
            return
        
        self.logger.debug(f"Displaying {command_type.value} results: {type(results).__name__}")
            
        if command_type == CommandType.LIST and isinstance(results, list) and results:
            # Tabular display for lists
            if isinstance(results[0], dict):
                headers = list(results[0].keys())
                self.user_interface.display_results_tabular(results, headers)
            else:
                for result in results:
                    self.user_interface.display_results(result)
                    
        elif command_type == CommandType.DETAIL and isinstance(results, dict):
            # Key-value display for details
            self.user_interface.display_key_values_list(results)
            
        elif isinstance(results, list):
            # List of results
            for result in results:
                if result is not None:
                    self.user_interface.display_results(result)
        else:
            # Single result
            self.user_interface.display_results(results)