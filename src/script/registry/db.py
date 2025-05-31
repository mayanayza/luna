"""
Database registry that manages database implementations.
"""

import os
from typing import Optional

from src.script.common.decorators import register_handlers
from src.script.common.enums import CommandType, EntityType
from src.script.entity._base import EntityRef
from src.script.entity.db import Database
from src.script.input.factory import InputFactory
from src.script.registry._registry import ListableEntityRegistry


@register_handlers(
    {
        'input_method_name': 'get_clear_inputs',
        'handler_method_name': 'handle_clear',
        'command_type': CommandType.CLEAR,
    }
)
class DatabaseRegistry(ListableEntityRegistry):
    
    def __init__(self, manager):
        
        super().__init__(EntityType.DB, Database, manager)
        
        self._active_db_ref: Optional[EntityRef] = None        
        self.module_loader.load('src.script.db')

        try:
            # Get database type from environment or config, default to 'sqlite'
            db_type = os.environ.get('DB_TYPE', 'sqlite')
            
            # Set up the specified database
            db = self.get_by_name(db_type)
            if not db:
                self.logger.error(f"Database implementation not found: {db_type}.")
            
            # Set as active database
            self.active_db_ref = db.ref
                                
            # Initialize the database
            if not db.initialize():
                self.logger.error(f"Failed to initialize database: {db.name}")
                        
            self.logger.info(f"Database setup complete with {db.name}")
        except Exception as e:
            self.logger.error(f"Error setting up database: {e}")
            import traceback
            self.logger.error(traceback.format_exc())

    @property
    def active_db_ref(self) -> EntityRef:
        return self._active_db_ref

    @active_db_ref.setter
    def active_db_ref(self, val) -> bool:
        db = self.get_by_ref(val)
        if db:
            self._active_db_ref = val
            self.manager.update_db(val)
            self.logger.debug(f"Set active database to: {db.name}")
            return True
        else:
            self.logger.error(f"Database not found for ref: {val}")
            return False

     ######                                ##
       ##                                  ##
       ##     ## ###   ######   ##   ##  ######    #####
       ##     ###  ##  ##   ##  ##   ##    ##     ##
       ##     ##   ##  ##   ##  ##   ##    ##      ####
       ##     ##   ##  ##   ##  ##  ###    ##         ##
     ######   ##   ##  ######    ### ##     ###   #####
                       ##

    @classmethod
    def get_clear_inputs(cls, registry, **kwargs):
        return InputFactory.no_input_needed(handler_registry=registry.handler_registry)

     ##   ##                         ##   ###
     ##   ##                         ##    ##
     ##   ##   ######  ## ###    ######    ##      #####   ## ###    #####
     #######  ##   ##  ###  ##  ##   ##    ##     ##   ##  ###      ##
     ##   ##  ##   ##  ##   ##  ##   ##    ##     #######  ##        ####
     ##   ##  ##  ###  ##   ##  ##   ##    ##     ##       ##           ##
     ##   ##   ### ##  ##   ##   ######   ####     #####   ##       #####

    @classmethod
    def handle_clear(cls, registry, **kwargs):
        active_db = registry.get_by_ref(registry.active_db_ref)
        return active_db.clear()

    def reset(self) -> bool:
       
        try:
            # Close all database connections
            self.close_all()
            
            # Reset active database reference
            self._active_db_ref = None
            
            # Reset setup complete flag
            self._setup_complete = False
            
            self.logger.info("Database registry reset")
            return True
        except Exception as e:
            self.logger.error(f"Error resetting database registry: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def close_all(self):
        """Close all database connections."""
        for db in self.get_all_entities():
            try:
                db.close()
                self.logger.debug(f"Closed database: {db.name}")
            except Exception as e:
                self.logger.error(f"Error closing database {db.name}: {e}")
                import traceback
                self.logger.error(traceback.format_exc())