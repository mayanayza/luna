"""
Database registry that manages database implementations.
"""

import os
from typing import Optional

from entities.base import EntityRef
from entities.database.entity import DatabaseBase
from registries.base import Registry


class DatabaseRegistryBase(Registry):

    def __init__(self, manager):
        
        super().__init__(manager)
        
        self._active_db_ref: Optional[EntityRef] = None        

        try:
            # Get database type from environment or config, default to 'sqlite'
            db_type = os.environ.get('DB_TYPE', 'sqlite')

            # Set up the specified database
            db: DatabaseBase = self.get_by_name(db_type)
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
    def active_db_ref(self, val):
        db = self.get_by_ref(val)
        if db:
            self._active_db_ref = val
            self.manager.update_db(val)
            self.logger.debug(f"Set active database to: {db.name}")
        else:
            self.logger.error(f"Database not found for ref: {val}")

    def get_active_db(self):
        return self.get_by_ref( self._active_db_ref )

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