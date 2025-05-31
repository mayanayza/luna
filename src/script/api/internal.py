from typing import Any, Dict, List

from src.script.api._input_converter import ApiInputConverter
from src.script.api._ui import UserInterface
from src.script.common.enums import CommandType, EntityQuantity
from src.script.entity.api import Api, ApiResult
from src.script.input.input import Input

   ##     ######   ######
   ##     ##   ##    ##
  ####    ##   ##    ##
  ## #    ######     ##
 ######   ##         ##
 ##   #   ##         ##
###   ##  ##       ######


class InternalApi(Api):
    """Internal API for programmatic command execution with batch support"""
    
    def __init__(self, registry, **kwargs):
        super().__init__(registry, **kwargs)
        
    @property
    def input_converter(self):
        return InternalInputConverter()
    
    @property
    def user_interface(self):
        return InternalUserInterface()

    def get_entity_quantity_for_command(self, command_type: CommandType) -> EntityQuantity:
        """
        Internal API entity quantity settings - optimized for programmatic use.
        Generally allows multiple entities for bulk operations.
        """
        # Internal API optimized for batch operations where possible
        internal_quantities = {
            # Allow bulk operations for efficiency
            CommandType.DELETE: EntityQuantity.MULTIPLE,  # Can delete multiple entities at once
            CommandType.RENAME: EntityQuantity.SINGLE,    # Renaming multiple doesn't make sense
            CommandType.DETAIL: EntityQuantity.MULTIPLE,  # Can get details for multiple entities
            CommandType.LIST: EntityQuantity.OPTIONAL_MULTIPLE,  # Can list all or filtered
            
            # Integration operations
            CommandType.ADD_INTEGRATION: EntityQuantity.MULTIPLE,     # Add to multiple projects
            CommandType.REMOVE_INTEGRATION: EntityQuantity.MULTIPLE, # Remove from multiple projects
        }
        
        return internal_quantities.get(command_type, EntityQuantity.MULTIPLE)  # Default to multiple for bulk ops

    def start(self):
        """Internal API doesn't need to start a session"""
        pass

    def execute_single(self, 
                      entity_type: str, 
                      command_type: str, 
                      **params) -> ApiResult:
        """
        Convenience method for executing single operations
        
        Args:
            entity_type: The entity type to operate on
            command_type: The command to execute  
            **params: Parameters for the operation
            
        Returns:
            ApiResult containing the single operation result
        """
        # Convert single operation to batch format
        param_list = [params]
        
        batch_result = self.execute_command(entity_type, command_type, param_list)
        
        if batch_result.is_failure:
            return batch_result
        
        # Extract single result from batch
        batch = batch_result.value
        if batch.total_count == 0:
            return ApiResult.failure("No operations executed", code="no_operations")
        
        single_operation = batch.operation_results[0]
        if single_operation.is_success:
            return ApiResult.success(single_operation.value)
        else:
            return ApiResult.failure(
                message=single_operation.error_message,
                code=single_operation.error.code if single_operation.error else "operation_failed"
            )

    def execute_batch(self, 
                     entity_type: str, 
                     command_type: str, 
                     param_sets: List[Dict[str, Any]]) -> ApiResult:
        """
        Convenience method for executing batch operations with explicit parameter sets
        
        Args:
            entity_type: The entity type to operate on
            command_type: The command to execute
            param_sets: List of parameter dictionaries for batch execution
            
        Returns:
            ApiResult containing BatchResult
        """
        return self.execute_command(entity_type, command_type, param_sets)

    def display_results(self, command_type: CommandType, results: Any) -> None:
        """Internal API doesn't display - just log if needed"""
        self.logger.debug(f"Internal API result for {command_type.value}: {results}")

 ######                                ##       ####                                                  ##
   ##                                  ##      ##  ##                                                 ##
   ##     ## ###   ######   ##   ##  ######   ##        #####   ## ###   ### ###   #####   ## ###   ######    #####   ## ###
   ##     ###  ##  ##   ##  ##   ##    ##     ##       ##   ##  ###  ##   ## ##   ##   ##  ###        ##     ##   ##  ###
   ##     ##   ##  ##   ##  ##   ##    ##     ##       ##   ##  ##   ##   ## ##   #######  ##         ##     #######  ##
   ##     ##   ##  ##   ##  ##  ###    ##      ##  ##  ##   ##  ##   ##    ###    ##       ##         ##     ##       ##
 ######   ##   ##  ######    ### ##     ###     ####    #####   ##   ##    ###     #####   ##          ###    #####   ##
                   ##

class InternalInputConverter(ApiInputConverter):
    """Input converter for internal API - only handles input collection/conversion"""
    
    def to_api_spec(self, input_obj: Input) -> Dict[str, Any]:
        """Internal API doesn't need specs - not used"""
        return {"name": input_obj.name}
    
    def collect_inputs(self, 
                  input_obj: Input, 
                  provided_inputs: Dict[str, Any],
                  context: Dict[str, Any] = None) -> ApiResult:
        """Returns ApiResult[Dict] instead of dict"""
        try:
            
            # Check for missing inputs
            missing_inputs = self.check_missing_inputs(input_obj, provided_inputs)
            
            if missing_inputs:
                return ApiResult.failure(
                    message=f"Missing required inputs: {missing_inputs}",
                    code="missing_inputs"
                )
            
            # Apply inputs
            self._apply_inputs_to_input(input_obj, provided_inputs)
            
            # Validate
            validation_result = input_obj.validate_all()
            
            if validation_result.is_failure:
                error_details = []
                for field, errors in validation_result.field_errors.items():
                    for error in errors:
                        error_details.append(f"{field}: {error.message}")
                
                return ApiResult.failure(message=f"Validation failed: {'; '.join(error_details)}",code="validation_failed")
            
            # Commit
            try:
                if not input_obj.commit_all_values():
                    return ApiResult.failure(
                        message="Failed to commit input values",
                        code="commit_failed",
                        source="InternalInputConverter.collect_inputs"
                    )
            except Exception as e:
                return ApiResult.failure(
                    message=f"Commit failed: {str(e)}",
                    source="InternalInputConverter.collect_inputs"
                )
            
            # Return the collected inputs
            return ApiResult.success(provided_inputs)
            
        except Exception as e:
            return ApiResult.failure(message=str(e))

 ##   ##                             ######              ##                         ####
 ##   ##                               ##                ##                        ##
 ##   ##   #####    #####   ## ###     ##     ## ###   ######    #####   ## ###   #####     ######   #####    #####
 ##   ##  ##       ##   ##  ###        ##     ###  ##    ##     ##   ##  ###       ##      ##   ##  ##       ##   ##
 ##   ##   ####    #######  ##         ##     ##   ##    ##     #######  ##        ##      ##   ##  ##       #######
 ##   ##      ##   ##       ##         ##     ##   ##    ##     ##       ##        ##      ##  ###  ##       ##
  #####   #####     #####   ##       ######   ##   ##     ###    #####   ##        ##       ### ##   #####    #####


class InternalUserInterface(UserInterface):
    """Minimal user interface for internal API"""
    
    def __init__(self):
        import logging
        self.logger = logging.getLogger(__name__)
    
    def respond(self, message: str, level: str = "info") -> None:
        getattr(self.logger, level)(message)
    
    def display_results(self, results: Any) -> None:
        self.logger.debug(f"Internal API result: {results}")
    
    def display_results_tabular(self, results, headers):
        self.logger.debug(f"Internal API tabular result: {len(results)} rows")
    
    def display_key_values_list(self, details: Dict[str, Any]) -> None:
        self.logger.debug(f"Internal API key-value result: {details}")
    
    def display_validation_errors(self, validation_errors: Dict[str, Any]) -> None:
        self.logger.error(f"Internal API validation errors: {validation_errors}")