"""
Database registry that manages database implementations.
"""

import os
from typing import Optional

from src.script.entity._base import EntityRef
from src.script.entity._db import Database
from src.script.registry._base import CommandableRegistry


class DatabaseRegistry(CommandableRegistry):
    """
    Registry for database implementations.
    
    This class extends the Registry to manage database implementations
    and handles database lifecycle management.
    """
    
    def __init__(self):
        """
        Initialize the database registry.
        
        This loads database implementations and initializes basic structures
        but does not set up any active database yet.
        """
        super().__init__('database', Database)
        
        self._active_db_ref: Optional[EntityRef] = None
    
    def load(self):
        """
        Setup the database system - initialize a database and create schema.
        
        This method:
        1. Loads available database implementations
        2. Selects a database implementation based on environment variables or config
        3. Sets it as the active database
        4. Initializes the database
        5. Creates schema
        
        Args:
            config: Optional database configuration
            
        Returns:
            True if setup was successful
        """
        
        self.load_from_module('src.script.db')

        try:
            # Get database type from environment or config, default to 'sqlite'
            db_type = os.environ.get('DB_TYPE', 'sqlite')
            
            # Set up the specified database
            db = self.get_by_name(db_type)
            if not db:
                self.logger.error(f"Database implementation not found: {db_type}.")
                return False
            
            # Set as active database
            self.active_db_ref = db.ref
                                
            # Initialize the database
            if not db.initialize():
                self.logger.error(f"Failed to initialize database: {db.name}")
                return False
                        
            self.logger.info(f"Database setup complete with {db.name}")
            return True
        except Exception as e:
            self.logger.error(f"Error setting up database: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False

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
                        
    def handle_clear(self):
        db = self.get_by_ref(self.active_db_ref)
        db.clear()

    def reset(self) -> bool:
        """
        Reset the database by closing all connections and.
        
        Returns:
            True if reset was successful
        """
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