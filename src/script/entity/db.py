"""
Database base class that integrates PyDAL with the registry pattern.
"""

import logging
import os
import threading
from abc import abstractmethod
from typing import TypeVar

from pydal import DAL, Field
from src.script.common.constants import EntityType
from src.script.common.decorators import classproperty
from src.script.entity._entity import ListableEntity, StorableEntity

# Type aliases for common database types
T = TypeVar('T')

class Database(ListableEntity):
    """
    Base class for database implementations that integrates with the registry pattern.
    Uses PyDAL as the underlying database abstraction layer.
    
    This class extends EntityBase to be managed by the registry system.
    """
    
    def __init__(self, registry, name: str, **kwargs):
        """
        Initialize the database.
        
        Args:
            registry: The registry this database belongs to
        """
        # Initialize ModuleEntity first
        super().__init__(registry, name)
        
        self._init_env_vars()

        self._db_dir = self.env.get('dir', os.path.expanduser("~/.luna/data"))
        self._db_name = self.env.get('name', 'luna')

        # DB-specific attributes
        self._connection_string = None
        self._db_path = None
        
        # Database connection is not initialized yet
        self._dal = None

        self._lock = threading.RLock()

    @classproperty
    def type(self):
        return EntityType.DB

    @classproperty
    def short_name(self):
        return 'db'

    @property
    def db_dir(self) -> str:
        return self._db_dir

    @property
    def db_path(self) -> str:
        return self._db_path
    
    @property
    def db_name(self) -> str:
        return self._db_name
    
    @property
    def connection_string(self):
        return self._connection_string
    
    @property
    def dal(self) -> DAL:
        return self._dal

    @dal.setter
    def dal(self, val) -> None:
        self._dal = val

    def clear(self, **kwargs) -> bool:
        """
        Reset the database to a fresh state by deleting all data from all tables.
        This preserves the table structure but removes all records.
        
        Returns:
            True if successful
        """
        try:
            if not self.dal:
                self.logger.error("Database connection not initialized")
                return False
            
            table_definitions = self._get_table_definitions()
            
            with self.transaction():
                # Delete all data from each table
                for table_name in table_definitions.keys():
                    if hasattr(self.dal, table_name):
                        table = getattr(self.dal, table_name)
                        # Delete all records from the table
                        deleted_count = self.dal(table).delete()
                        self.logger.info(f"Deleted {deleted_count} records from table '{table_name}'")
                    else:
                        self.logger.warning(f"Table '{table_name}' not found during reset")
            
            self.logger.info(f"Successfully reset database {self.name} - all data cleared")
            return "Success"
            
        except Exception as e:
            self.logger.error(f"Error resetting database {self.name}: {e}")
            try:
                self.dal.rollback()
            except:
                pass
            return "Could not reset database"

    def _init_env_vars(self) -> None:
        # Get all environment variables with DB_ prefix
        self.env = {}
        for key, value in os.environ.items():
            if key.startswith('DB_'):
                # Convert to lowercase and remove DB_ prefix for config keys
                config_key = key[3:].lower()
                self.env[config_key] = value

    def _table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database. Override in subclasses for DB-specific logic."""
        try:
            # Generic approach - try to query the table
            table = getattr(self.dal, table_name, None)
            if table is None:
                return False
            self.dal(table).count()
            return True
        except Exception:
            return False

    def _get_table_definitions(self):
        """Get the table definitions for all required tables."""
        # Return field specifications as dictionaries instead of Field objects
        # This allows us to create fresh Field objects when needed
        return {
            EntityType.PROJECT.value: [
                ('id', 'id'),
                ('uuid', 'string'),
                ('name', 'string'),
                ('date_created', 'string'),
                ('title', 'string'),
                ('emoji', 'string'),
                ('config', 'json'),
            ],
            EntityType.INTEGRATION.value: [
                ('id', 'id'),
                ('uuid', 'string'),
                ('name', 'string'),
                ('date_created', 'string'),
                ('config', 'json'),
                ('base_module', 'string'),
                ('title', 'string'),
                ('emoji', 'string'),
            ],
            EntityType.PROJECT_INTEGRATION.value: [
                ('id', 'id'),
                ('uuid', 'string'),
                ('name', 'string'),
                ('config', 'json'),
                ('date_created', 'string'),
                ('project_uuid', 'string'),
                ('integration_uuid', 'string'),
            ]
        }

    def _create_field_objects(self, field_specs):
        """Create fresh Field objects from field specifications."""
        return [Field(name, field_type) for name, field_type in field_specs]

    def _create_tables(self) -> bool:
        """Create tables if they don't exist, with proper error handling."""
        try:
            table_definitions = self._get_table_definitions()
            
            # Define all tables with fresh Field objects and proper migration
            for table_name, field_specs in table_definitions.items():
                if not hasattr(self.dal, table_name):
                    self.logger.debug(f"Defining '{table_name}' table")
                    field_defs = self._create_field_objects(field_specs)
                    self.dal.define_table(table_name, *field_defs, migrate=True)
            return True        
        except Exception as e:
            self.logger.error(f"Error creating tables: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            self.dal.rollback()
            return False

    def transaction(self):
        class TransactionContext:
            def __init__(self, db):
                self.db = db
                
            def __enter__(self):
                self.db.logger.debug("Starting database transaction")
                self.db._lock.acquire()
                return self
                
            def __exit__(self, exc_type, exc_val, exc_tb):
                try:
                    if exc_type is not None:
                        self.db.logger.warning("Rolling back database transaction")
                        self.db.dal.rollback()
                        return False
                    else:
                        self.db.logger.debug("Committing database transaction")
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
            self.logger.debug(f"Initializing database connection: {self._connection_string}")
            self.dal = DAL(
                self._connection_string, 
                folder=self._db_dir, 
                migrate=True,
                pool_size=0,  # Good default for most databases
                check_reserved=['all']
            )

            if logging.getLogger().level == logging.DEBUG:
                self.dal._debug = True
            
            # Verify connection was established
            if not self.dal:
                self.logger.error("Failed to initialize database connection")
                return False

            # Apply any database-specific configurations
            if not self._configure_database():
                self.logger.warning("Database configuration had issues, but continuing...")

            # Create tables with proper error handling
            if not self._create_tables():
                self.logger.error("Failed to create required tables")
                return False
                        
            self.logger.info(f"Initialized {self.name} database at: {self._db_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing database {self.name}: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False

    @abstractmethod
    def _configure_database(self) -> bool:
        """
        Apply database-specific configurations. Override in subclasses.
        
        Returns:
            True if successful, False if there were issues (but not fatal)
        """
        # Default implementation does nothing
        return True

    def upsert(self, table_name: str, entity: StorableEntity) -> bool:
        """
        Update if exists by ID, otherwise insert.
        
        Args:
            table_name: Name of the table
            entity: The entity to save
            
        Returns:
            True if successful
        """
        try:
            table = self.dal[table_name]

            record = {
                'name': entity.name,
                'date_created': entity.date_created,
                'uuid': entity.uuid,
                'config': entity.config.to_dict(),
                **entity.db_fields
            }

            self.logger.debug(f"Upserting {record}")
            
            # Check if entity exists
            with self.transaction():
                existing = self.dal(table['id'] == entity.db_id).select().first()
            
            if existing:
                # Update existing document (exclude id_field)
                with self.transaction():
                    self.dal(table['id'] == entity.db_id).update(**record)
                return True
            
            # Insert new document
            with self.transaction():
                table.insert(**record)
            self.logger.debug(f"Upserted record {record} to table {table_name}")
            return True
        except Exception as e:
            self.logger.error(f"Error in upsert: {e}")
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