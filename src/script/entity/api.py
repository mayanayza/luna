# api.py - Simplified without entity resolution methods

from abc import abstractmethod
from typing import Any

from src.script.common.constants import EntityType
from src.script.common.decorators import classproperty
from src.script.entity._entity import ListableEntity


class Api(ListableEntity):
    def __init__(self, registry, name: str, **kwargs):
        super().__init__(registry, name, **kwargs)
    
    @classproperty
    def type(self):
        return EntityType.API

    @property
    def input_interface(self):
        if hasattr(self, '_input_interface'):
            return self._input_interface
        else:
            raise NotImplementedError("No input interface implemented")

    @property
    def user_interface(self):
        if hasattr(self, '_user_interface'):
            return self._user_interface
        else:
            raise NotImplementedError("No user interface implemented")
    
    @abstractmethod
    def start(self):
        """Start the API with the provided application context."""
        pass
    
    def display_results(self, command: str, results: Any) -> None:
        """Display command results appropriately based on command type"""
        if not results:
            self.user_interface.respond("No results returned")
            return
            
        if command == 'list' and isinstance(results, list) and results:
            # Tabular display for lists
            if isinstance(results[0], dict):
                headers = list(results[0].keys())
                self.user_interface.display_results_tabular(results, headers)
            else:
                for result in results:
                    self.user_interface.display_results(result)
                    
        elif command == 'detail' and isinstance(results, dict):
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