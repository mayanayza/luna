"""
SQLite implementation using PyDAL as the underlying database layer.
Requires SQLite 3.38.0+ for proper JSON support.
"""

import os

from src.script.entity._db import Database


class SQLiteDatabase(Database):
    """SQLite implementation of the Database interface using PyDAL."""
    
    def __init__(self, registry):
        """
        Initialize a SQLite database.
        
        Args:
            registry: The registry this database belongs to
        """
        # Set name before parent init for proper registration
        self.name = 'sqlite'

        # Initialize base class
        super().__init__(registry)

        self._db_path = os.path.join(self._db_dir, f"{self._db_name}.sqlite")
        self._connection_string = f"sqlite://{self._db_path}"

    def initialize(self) -> bool:
        """
        Initialize the SQLite database, adding SQLite-specific configurations.
        
        Returns:
            True if successful
        """
        # First call the parent initialization
        if not super().initialize():
            return False
            
        try:
            # Set SQLite-specific pragmas
            self.dal.executesql('PRAGMA journal_mode=WAL;')
            self.dal.executesql('PRAGMA foreign_keys=ON;')
            return True
        except Exception as e:
            self.logger.error(f"Error configuring SQLite settings: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False