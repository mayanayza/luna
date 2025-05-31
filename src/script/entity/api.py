# Enhanced api.py - Complete file with smart input collection

import time
from abc import abstractmethod
from typing import Any, Dict, List, TypeVar, Union

from src.script.common.decorators import classproperty
from src.script.common.enums import CommandType, EntityQuantity, EntityType
from src.script.common.results import (
    ApiResult,
    BatchOperationResult,
    BatchResult,
    HandlerResult,
)
from src.script.entity._entity import ListableEntity
from src.script.input.factory import InputFactory
from src.script.input.input import Input, InputField, InputPermissions

T = TypeVar('T')

class Api(ListableEntity):
    """Base API class with input collection and command execution"""
    
    def __init__(self, registry, **kwargs):
        super().__init__(registry, **kwargs)
        self.current_command_type = None
    
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

    def get_entity_quantity_for_command(self, command_type: CommandType) -> EntityQuantity:
        """
        Get the entity quantity setting for a specific command.
        
        Args:
            command_type: The command type
            
        Returns:
            EntityQuantity enum value:
            - SINGLE: exactly one entity
            - MULTIPLE: one or more entities
            - OPTIONAL_MULTIPLE: zero or more entities
        """
        # Default implementation - subclasses can override
        return EntityQuantity.SINGLE

    def execute_command(self, 
                       entity_type: Union[EntityType, str], 
                       command_type: Union[CommandType, str], 
                       params: List[Dict[str, Any]]) -> ApiResult:
        """
        Execute a command with input collection and command execution
        
        Args:
            entity_type: The entity type to operate on
            command_type: The command to execute
            params: List of parameter dictionaries, each representing one operation
            
        Returns:
            ApiResult containing list of individual results
        """
        start_time = time.time()
        
        try:
            # Normalize to enums if strings provided
            if isinstance(entity_type, str):
                entity_type = EntityType(entity_type)
            if isinstance(command_type, str):
                command_type = CommandType(command_type)

            # Store current command type for entity quantity decisions
            self.current_command_type = command_type

            self.logger.info(f"Executing {command_type.value} on {entity_type.value} with {len(params)} parameter sets")
            
            # 1. Prepare command template
            prep_result = self._prepare_command(entity_type, command_type)
            if prep_result.is_failure:
                return prep_result

            input_obj = prep_result.value
            
            # 2. Process batch parameters with smart input collection
            batch_result = self._process_batch_params(input_obj, params, entity_type, command_type)
            if batch_result.is_failure:
                return batch_result
            
            param_sets = batch_result.value
            
            # 3. Execute each parameter set independently
            batch_result = BatchResult.success([])
            
            for i, param_set in enumerate(param_sets):
                self.logger.debug(f"Processing parameter set {i+1}/{len(param_sets)}: {param_set}")
                
                try:
                    # Create fresh input object for this parameter set
                    input_obj = self._create_input_from_template(input_obj)
                    
                    # Collect inputs for this specific parameter set
                    collect_result = self._collect_inputs(input_obj, param_set)
                    if collect_result.is_failure:
                        self.logger.warning(f"Parameter set {i+1} failed input collection: {collect_result.error_message}")
                        operation_result = BatchOperationResult.failure(
                            param_set_index=i,
                            params=param_set,
                            message=f"Input collection failed: {collect_result.error_message}",
                            code="input_collection_failed"
                        )
                        batch_result.add_operation_result(operation_result)
                        continue
                    
                    collected_inputs = collect_result.value
                    
                    # Execute handlers for this parameter set
                    handler_result = self._execute_handlers(input_obj, collected_inputs)
                    if handler_result.is_failure:
                        self.logger.warning(f"Parameter set {i+1} failed handler execution: {handler_result.error_message}")
                        operation_result = BatchOperationResult.failure(
                            param_set_index=i,
                            params=param_set,
                            message=f"Handler execution failed: {handler_result.error_message}",
                            code="handler_execution_failed"
                        )
                        batch_result.add_operation_result(operation_result)
                        continue
                    
                    # Process results for this parameter set
                    process_result = self._process_results(handler_result.value, command_type, input_obj, collected_inputs)
                    if process_result.is_failure:
                        self.logger.warning(f"Parameter set {i+1} failed result processing: {process_result.error_message}")
                        operation_result = BatchOperationResult.failure(
                            param_set_index=i,
                            params=param_set,
                            message=f"Result processing failed: {process_result.error_message}",
                            code="result_processing_failed"
                        )
                        batch_result.add_operation_result(operation_result)
                        continue
                    
                    # Success case
                    operation_result = BatchOperationResult.success(
                        param_set_index=i,
                        params=param_set,
                        value=process_result.value
                    )
                    batch_result.add_operation_result(operation_result)
                    
                except Exception as e:
                    self.logger.warning(f"Parameter set {i+1} failed with exception: {e}")
                    operation_result = BatchOperationResult.failure(
                        param_set_index=i,
                        params=param_set,
                        message=f"Unexpected error: {str(e)}",
                        code="unexpected_error"
                    )
                    batch_result.add_operation_result(operation_result)
            
            # 4. Summary logging
            total_time = time.time() - start_time
            self.logger.info(f"Command {command_type.value} completed in {total_time:.3f}s: {batch_result.success_count} successful, {batch_result.failure_count} failed")
            
            return ApiResult.success(batch_result)
            
        except Exception as e:
            total_time = time.time() - start_time
            self.logger.error(f"Command {command_type.value} failed after {total_time:.3f}s: {e}", exc_info=True)
            return ApiResult.failure(
                message=str(e),
                code="batch_command_execution_failed"
            )

    def _process_batch_params(self, 
                             input_obj: Input, 
                             params: List[Dict[str, Any]], 
                             entity_type: EntityType, 
                             command_type: CommandType) -> ApiResult:
        """
        Process batch parameters with smart entity selection and field collection
        """
        try:
            # Check if we need entity targets
            system_handler = self.handler_registry.get_system_handler_for_entity_and_command_type(
                entity_type, command_type
            )
            
            if not system_handler or not system_handler.needs_target:
                return ApiResult.success(params)
            
            entity_param_name = system_handler.get_entity_param_name()
            
            # Analyze what we have and what we need using the existing input_obj
            required_fields = self._get_required_fields(input_obj, entity_param_name)
            first_param_set = params[0] if params else {}
            
            has_entities = entity_param_name in first_param_set and first_param_set[entity_param_name] is not None
            provided_fields = {k for k, v in first_param_set.items() 
                              if k != entity_param_name and v is not None}
            missing_fields = required_fields - provided_fields
            
            # Step 1: Collect entities if not provided
            if not has_entities:
                entities = self._collect_entities(entity_type)
                if not entities:
                    return ApiResult.failure("No entities selected", "no_entities")
            else:
                # Extract entities from existing parameter sets
                entities = self._extract_entities_from_params(params, entity_param_name)
            
            # Step 2: Create parameter sets for each entity with provided fields
            expanded_params = []
            for entity in entities:
                param_set = first_param_set.copy()
                param_set[entity_param_name] = entity
                expanded_params.append(param_set)
            
            # Step 3: Collect any missing required fields (these are collected individually per entity)
            if missing_fields:
                expanded_params = self._collect_missing_fields_per_entity(expanded_params, input_obj, missing_fields)
            
            return ApiResult.success(expanded_params)
                
        except Exception as e:
            return ApiResult.failure(message=f"Parameter processing failed: {str(e)}")

    def _get_required_fields(self, input_obj: Input, entity_param_name: str) -> set:
        """Get all required field names (excluding entity field and hidden fields)"""
        required_fields = set()
        for field_name, field in input_obj.children.items():
            if (isinstance(field, InputField) and 
                field.required and 
                not getattr(field, 'hidden', False) and 
                field_name != entity_param_name):
                required_fields.add(field_name)
        return required_fields

    def _collect_entities(self, entity_type: EntityType) -> List[Any]:
        """Collect entity targets from user"""
        quantity_setting = self.get_entity_quantity_for_command(self.current_command_type)
        return self._collect_entity_targets(entity_type, quantity_setting, 1)

    def _extract_entities_from_params(self, params: List[Dict[str, Any]], entity_param_name: str) -> List[Any]:
        """Extract entities from existing parameter sets"""
        entities = []
        for param_set in params:
            entity = param_set.get(entity_param_name)
            if entity:
                if isinstance(entity, list):
                    entities.extend(entity)
                else:
                    entities.append(entity)
        return entities

    def _collect_missing_fields_per_entity(self, param_sets: List[Dict[str, Any]], input_obj: Input, missing_fields: set) -> List[Dict[str, Any]]:
        """Collect missing fields individually for each entity"""
        
        missing_field_input = self._create_fields_input(input_obj, missing_fields)
        entity_param_name = self._get_entity_param_name(input_obj)
        
        for i, param_set in enumerate(param_sets):
            entity = param_set.get(entity_param_name)
            entity_name = getattr(entity, 'display_title', f'entity {i+1}')
            
            self.user_interface.respond(f"Configuring {entity_name}...")
            
            context = {"api_type": self.name, "target_entity": entity}
            collection_result = self.input_converter.collect_inputs(missing_field_input, param_set, context)
            
            if collection_result.is_failure:
                raise Exception(f"Field collection failed for {entity_name}: {collection_result.error_message}")
            
            param_set.update(collection_result.value)
        
        return param_sets

    def _create_fields_input(self, input_obj: Input, field_names: set) -> Input:
        """Create input object with only specified fields from the existing input_obj"""
        
        field_children = []
        for field_name in field_names:
            if field_name in input_obj.children:
                field_children.append(input_obj.children[field_name])
        
        return Input(
            name=f"{input_obj.name}_fields",
            title="Configure Fields",
            handler_registry=input_obj.handler_registry,
            children=field_children
        )

    def _get_entity_param_name(self, input_obj: Input) -> str:
        """Get the entity parameter name from the input_obj"""
        # Find the entity field (field with choices that are entities)
        for field_name, field in input_obj.children.items():
            if isinstance(field, InputField) and hasattr(field, 'choices') and callable(field.choices):
                return field_name
        return None

    def _collect_entity_targets(self, 
                               entity_type: EntityType, 
                               quantity_setting: EntityQuantity, 
                               param_set_count: int) -> List[Any]:
        """
        Collect entity targets based on quantity setting
        
        Args:
            entity_type: Type of entities to select
            quantity_setting: Single, multiple, or optional multiple
            param_set_count: Number of parameter sets that need entities
            
        Returns:
            List of entity targets
        """
        try:
            # Create entity selector
            registry = self.handler_registry.manager.get_by_entity_type(entity_type)
            
            selector_config = {
                'title': f'Select {entity_type.value}(s)',
                'description': f'Choose {entity_type.value}(s) for this operation',
                'allow_multiple': quantity_setting in [EntityQuantity.MULTIPLE, EntityQuantity.OPTIONAL_MULTIPLE],
                'required': quantity_setting != EntityQuantity.OPTIONAL_MULTIPLE
            }
            
            entity_selector_field = InputFactory.entity_target_selector_field(
                name='entities',
                registry=registry,
                **selector_config
            )
            
            # Create temporary input for entity collection
            temp_input = Input('entity_collection', title='Entity Selection')
            temp_input.add_child(entity_selector_field)
            
            # Collect entity targets
            context = {"api_type": self.name}
            collect_result = self.input_converter.collect_inputs(temp_input, {}, context=context)
            
            if collect_result.is_failure:
                self.logger.error(f"Failed to collect entity targets: {collect_result.error_message}")
                return []
            
            entities = collect_result.value.get('entities', [])
            if not isinstance(entities, list):
                entities = [entities] if entities else []
            
            return entities
            
        except Exception as e:
            self.logger.error(f"Entity target collection failed: {e}")
            return []

    def _prepare_command(self, 
                        entity_type: EntityType, 
                        command_type: CommandType) -> ApiResult:
        """
        Prepare command for execution - find handlers and prepare input object template
        
        Args:
            entity_type: The entity type enum
            command_type: The command type enum
            
        Returns:
            ApiResult containing input object template
        """        
        try:
            system_handler = self.handler_registry.get_system_handler_for_entity_and_command_type(
                entity_type, command_type
            )
            
            if not system_handler:
                return ApiResult.failure(
                    message=f"No system handler found for {entity_type.value}.{command_type.value}",
                    code="handler_not_found"
                )

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
                input_obj = self._add_target_selector(input_obj, system_handler, entity_type, command_type)
                self.logger.debug("Added target selector to input object")

            return ApiResult.success(input_obj)
        except Exception as e:
            return ApiResult.failure(message=str(e))

    def _add_target_selector(self, input_obj: Input, handler, entity_type: EntityType, command_type: CommandType) -> Input:
        """Add entity target selector to input if needed"""
        # Temporarily allow field addition
        original_permissions = input_obj.permissions.to_dict()
        temp_permissions = original_permissions.copy()
        temp_permissions['can_add_fields'] = True
        input_obj.permissions = InputPermissions.from_dict(temp_permissions)
        
        # Get entity selector configuration from handler
        selector_config = handler.get_entity_selector_config()
        param_name = handler.get_entity_param_name()

        # Get the entity quantity setting for this API and command
        quantity_setting = self.get_entity_quantity_for_command(command_type)
        
        # Update selector configuration based on quantity setting
        if quantity_setting == EntityQuantity.SINGLE:
            selector_config['allow_multiple'] = False
            selector_config['required'] = True
        elif quantity_setting == EntityQuantity.MULTIPLE:
            selector_config['allow_multiple'] = True
            selector_config['required'] = True
        elif quantity_setting == EntityQuantity.OPTIONAL_MULTIPLE:
            selector_config['allow_multiple'] = True
            selector_config['required'] = False

        # Create entity selector field with updated configuration
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
                       provided_params: Dict[str, Any]) -> ApiResult:
        """Collect and validate inputs using the converter"""
        try:
            context = {"api_type": self.name}
            result = self.input_converter.collect_inputs(input_obj, provided_params, context=context)
            
            if result.is_success:
                return result
            else:
                return result
            
        except Exception as e:
            return ApiResult.failure(
                message=f"Input collection failed: {str(e)}",
                code="input_collection_failed"
            )

    def _execute_handlers(self, 
                         input_obj: Input, 
                         collected_inputs: Dict[str, Any]) -> ApiResult:
        """
        Execute all handlers with the collected inputs
        
        Args:
            input_obj: The input object (contains handler references)
            collected_inputs: All collected and validated inputs
            
        Returns:
            ApiResult containing handler results
        """
        handler_count = len(input_obj.handler_refs) if hasattr(input_obj, 'handler_refs') else 0
        self.logger.debug(f"Executing {handler_count} handlers with inputs: {list(collected_inputs.keys())}")
        
        try:
            context = {"api_type": self.__class__.__name__.lower()}
            handler_results = input_obj.invoke_handlers(context, **collected_inputs)

            # Check for any handler failures
            failed_handlers = [r for r in handler_results if r.is_failure]
            if failed_handlers:
                error_messages = [f"{r.name}: {r.error_message}" for r in failed_handlers]
                return ApiResult.failure(
                    message=f"Handler failures: {'; '.join(error_messages)}",
                    code="handler_execution_failed"
                )

            return ApiResult.success(handler_results)
            
        except Exception as e:
            return ApiResult.failure(message=f"Handler execution failed: {str(e)}")

    def _process_results(self, 
                        handler_results: List['HandlerResult'], 
                        command_type: CommandType,
                        input_obj: Input,
                        collected_inputs: Dict[str, Any]) -> ApiResult:
        """
        Process handler results and execute callbacks
        
        Args:
            handler_results: Results from handler execution
            command_type: Command type for logging/display
            input_obj: Input object (for callback access)
            collected_inputs: The inputs that were used
            
        Returns:
            Final processed result
        """
        try:                        
            # Process each handler result
            for handler_result in handler_results:
                if handler_result.is_success and handler_result.value:
                    self.display_results(command_type, handler_result.value)

            # Execute on_submit callback if present
            if hasattr(input_obj, 'on_submit') and input_obj.on_submit:
                try:
                    self.logger.debug("Executing on_submit callback")
                    callback_result = {
                        "success": True,
                        "results": handler_results,
                        "inputs": collected_inputs,
                        "internal_api": self.registry.manager.get_by_entity_type(EntityType.API).get_by_name('internal')
                    }
                    
                    input_obj.on_submit(**callback_result)
                    
                except Exception as e:
                    self.logger.error(f"On-submit callback failed: {e}")

            return ApiResult.success(handler_results)
            
        except Exception as e:
            return ApiResult.failure(message=f"Result processing failed: {str(e)}")
    
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