
from typing import Any, Dict

from src.script.api._enum import CommandType
from src.script.api._input_converter import ApiInputConverter
from src.script.api._ui import UserInterface
from src.script.entity.api import Api
from src.script.input.input import Input

   ##     ######   ######
   ##     ##   ##    ##
  ####    ##   ##    ##
  ## #    ######     ##
 ######   ##         ##
 ##   #   ##         ##
###   ##  ##       ######


class InternalApi(Api):
    """Internal API for programmatic command execution"""
    
    def __init__(self, registry, **kwargs):
        super().__init__(registry, **kwargs)
        
    @property
    def input_converter(self):
        return InternalInputConverter()
    
    @property
    def user_interface(self):
        return InternalUserInterface()

    def start(self):
        """Internal API doesn't need to start a session"""
        pass

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
                  context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Collect and validate inputs for internal execution
        """
        try:
            # Check for missing required inputs - Internal API fails fast
            missing_inputs = self.check_missing_inputs(input_obj, provided_inputs)
            
            if missing_inputs:
                return {
                    "success": False,
                    "error": f"Missing required inputs: {missing_inputs}"
                }
            
            # Load provided inputs into the input object using base class method
            self._apply_inputs_to_input(input_obj, provided_inputs)
            
            # Validate all inputs
            validation_result = input_obj.validate_all()
            if not validation_result["passed"]:
                return {
                    "success": False,
                    "validation_errors": validation_result["errors"]
                }
            
            # Commit all values
            if not input_obj.commit_all_values():
                return {
                    "success": False,
                    "error": "Failed to commit input values"
                }
            
            # Return the collected inputs
            return {
                "success": True,
                "inputs": provided_inputs
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

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