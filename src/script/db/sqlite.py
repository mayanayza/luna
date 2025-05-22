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
        # Initialize base class
        super().__init__(registry, 'sqlite')
        self._db_path = os.path.join(self._db_dir, f"{self._db_name}.sqlite")
        self._connection_string = f"sqlite://{self._db_path}"

    def _configure_database(self) -> bool:
        """Apply SQLite-specific pragmas for better performance and reliability."""
        try:
            self.dal.executesql('PRAGMA journal_mode=WAL;')
            self.dal.executesql('PRAGMA foreign_keys=ON;')
            self.dal.executesql('PRAGMA synchronous=NORMAL;')
            self.dal.executesql('PRAGMA temp_store=MEMORY;')
            self.dal.executesql('PRAGMA mmap_size=268435456;')  # 256MB
            return True
        except Exception as e:
            self.logger.warning(f"Could not set SQLite pragmas: {e}")
            return False