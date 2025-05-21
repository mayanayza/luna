"""
Database base class that integrates PyDAL with the registry pattern.
"""

import os
import threading
from typing import TypeVar

from pydal import DAL, Field
from src.script.constants import EntityType
from src.script.entity._base import EntityBase

# Type aliases for common database types
T = TypeVar('T')

class Database(EntityBase):
    """
    Base class for database implementations that integrates with the registry pattern.
    Uses PyDAL as the underlying database abstraction layer.
    
    This class extends EntityBase to be managed by the registry system.
    """
    
    def __init__(self, registry):
        """
        Initialize the database.
        
        Args:
            registry: The registry this database belongs to
        """
        # Initialize EntityBase first
        super().__init__(registry)
        self._init_env_vars()

        self._db_dir = self.env.get('dir', os.path.expanduser("~/.luna/data"))
        self._db_name = self.env.get('name', 'luna')

        # DB-specific attributes
        self._connection_string = None
        self._db_path = None
        
        # Database connection is not initialized yet
        self._dal = None

        self._lock = threading.RLock()
    
    @property
    def dal(self) -> DAL:
        """Get the PyDAL instance."""
        return self._dal

    @dal.setter
    def dal(self, val):
        self._dal = val

    def _init_env_vars(self) -> None:
        # Get all environment variables with DB_ prefix
        self.env = {}
        for key, value in os.environ.items():
            if key.startswith('DB_'):
                # Convert to lowercase and remove DB_ prefix for config keys
                config_key = key[3:].lower()
                self.env[config_key] = value

    def transaction(self):
        class TransactionContext:
            def __init__(self, db):
                self.db = db
                
            def __enter__(self):
                self.db._lock.acquire()
                return self
                
            def __exit__(self, exc_type, exc_val, exc_tb):
                try:
                    if exc_type is not None:
                        self.db.dal.rollback()
                        return False
                    else:
                        self.db.dal.commit()
                        return True
                finally:
                    # Always release the lock, even if an exception occurred
                    self.db._lock.release()

        
        return TransactionContext(self)
            
    def initialize(self) -> bool:
        """
        Initialize the database based on environment variables
        
        Returns:
            True if successful
        """
        try:
            if self.dal:
                self.close()

            # Ensure the parent directory exists
            db_dir = os.path.dirname(self._db_path)
            os.makedirs(db_dir, exist_ok=True)
            
            # Create the DAL connection
            self.logger.info(f"Initializing database connection: {self._connection_string}")
            self.dal = DAL(self._connection_string, folder=self._db_dir, migrate=True)
            
            # Verify connection was established
            if not self.dal:
                self.logger.error("Failed to initialize database connection")
                return False
                
            # Now create the tables
            self.logger.info("Creating 'project' table")
            self.dal.define_table(EntityType.PROJECT,
                Field('id', 'integer'),
                Field('name', 'string'),
                Field('date_created', 'string'),
                Field('data', 'json')
            )
                
            # Create integrations table
            self.logger.info("Creating 'integration' table")
            self.dal.define_table(EntityType.INTEGRATION,
                Field('id', 'integer'),
                Field('name', 'string'),
                Field('date_created', 'string'),
                Field('data', 'json'),
                Field('config', 'json'),
            )
                
            # Create project_integrations table
            self.logger.info("Creating 'project_integration' table")
            self.dal.define_table(EntityType.PROJECT_INTEGRATION,
                Field('id', 'integer'),
                Field('name', 'string'),
                Field('date_created', 'string'),
                Field('data', 'json'),
                Field('project_id', 'integer'),
                Field('integration_id', 'integer'),
            )
                        
            self.logger.info(f"Initialized {self.name} database at: {self._db_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error initializing database {self.name}: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False

    def upsert(self, table_name: str, entity: EntityBase) -> bool:
        """
        Update if exists by ID, otherwise insert.
        
        Args:
            table_name: Name of the table
            document: The document to save
            id_field: The field to use as the ID for existence check
            
        Returns:
            True if successful
        """
        try:
            table = self.dal[table_name]
            
            # Check if entity exists
            with self.transaction():
                existing = self.dal(table['id'] == entity.id).select().first()
            
            record = {
                'name': entity.name,
                'date_created': entity.date_created,
                'data': entity.data,
                **getattr(entity, 'storage_additional_fields', {})
            }

            if existing:
                # Update existing document (exclude id_field)
                with self.transaction():
                    self.dal(table['id'] == entity.id).update(**record)
                return True
            
            # Insert new document
            with self.transaction():
                table.insert(**record)
            return True
        except Exception as e:
            self.logger.error(f"Error in save: {e}")
            try:
                self.dal.rollback()
            except Exception as rollback_error:
                self.logger.error(f"Error in rollback: {rollback_error}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
        
    def close(self) -> None:
        """Close the database connection."""
        if self.dal:
            self.dal.close()
            self.dal = None
            self._initialized = False
            self.logger.info(f"Closed {self.name} database connection")