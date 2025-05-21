"""
Database registry that manages database implementations.
"""

import os
from typing import Optional

from src.script.entity._base import EntityRef
from src.script.entity._db import Database
from src.script.registry._base import Registry


class DatabaseRegistry(Registry):
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
            self.set_active_database_ref(db.ref)
                                
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

    def get_active_database_ref(self) -> Optional[EntityRef]:
        """
        Get a reference to the active database.
        
        Returns:
            EntityRef to the active database or None if not set
        """
        return self._active_db_ref
            
    def set_active_database_ref(self, db_ref: EntityRef) -> bool:
        """
        Set the active database by reference.
        
        Args:
            db_ref: The reference to the database to set as active
            
        Returns:
            True if successful
        """
        db = self.get_by_ref(db_ref)
        if db:
            self._active_db_ref = db_ref
            self.manager.update_db(db_ref)
            self.logger.info(f"Set active database to: {db.name}")
            return True
        else:
            self.logger.error(f"Database not found for ref: {db_ref}")
            return False
                    
    def reset(self) -> bool:
        """
        Reset the database registry by closing all connections.
        
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