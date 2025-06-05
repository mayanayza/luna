"""
Database base class that integrates PyDAL with the registry pattern.
"""

import os
import threading
from abc import abstractmethod

from pydal import DAL, Field
from common.enums import EntityType
from entities.base import Entity
from entities.mixins import UserNameablePropertyMixin, ReadOnlyNamePropertyMixin, ConfigPropertyMixin, \
    DatabasePropertyMixin


class DatabaseBase(Entity):

    def __init__(self, registry, **kwargs):
        super().__init__(registry, **kwargs)
        
        self._init_env_vars()

        # Database configuration
        self._db_dir = self.env.get('dir', os.path.expanduser("~/.luna/data"))
        self._db_name = self.env.get('name', 'luna')

        # Database connection attributes
        self._connection_string = None
        self._db_path = None
        self._dal = None
        self._lock = threading.RLock()

    @staticmethod
    def _generate_auto_name(**kwargs):
        """Custom name generation for implementations"""
        implementation_name = kwargs.get('filename', 'unknown')
        return implementation_name

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
    def lock(self):
        return self._lock
    
    @property
    def connection_string(self):
        return self._connection_string
    
    @property
    def dal(self) -> DAL:
        return self._dal

    @dal.setter
    def dal(self, val) -> None:
        self._dal = val

    def transaction(self):
        class TransactionContext:
            def __init__(self, db):
                self.db = db
                
            def __enter__(self):
                self.db.logger.debug("Starting database transaction")
                self.db.lock.acquire()
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
                    self.db.lock.release()

        
        return TransactionContext(self)

    @staticmethod
    def _get_table_definitions():
        # Get the table definitions for entities
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
                ('submodule', 'string'),
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

    @staticmethod
    def _create_field_objects(field_specs):
        """Create fresh Field objects from field specifications."""
        return [Field(name, field_type) for name, field_type in field_specs]

    def _create_tables(self) -> bool:
        """Create tables if they don't exist, with proper error handling."""
        try:
            table_definitions = DatabaseBase._get_table_definitions()
            
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

    @abstractmethod
    def _configure_database(self) -> bool:
        """Database-specific configuration - override in subclasses"""
        return True


    def clear(self) -> bool:
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
            return True
            
        except Exception as e:
            self.logger.error(f"Error resetting database {self.name}: {e}")
            try:
                self.dal.rollback()
            except Exception as e:
                self.logger.error(f"Error rolling back database {self.name}: {e}")
            return False

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
        except Exception as e:
            self.logger.error(f"Table {table_name} not found: {e}")
            return False


            
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
                pool_size=0,  # Good default for most implementations
                check_reserved=['all']
            )

            # if logging.getLogger().level == logging.DEBUG:
            #     self.dal._debug = True
            
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

    from typing import Union

    def upsert(self, table_name: str, entity: Union[Entity, ConfigPropertyMixin, DatabasePropertyMixin, UserNameablePropertyMixin, ReadOnlyNamePropertyMixin]) -> Union[bool, int]:
        """
        Update if exists by ID, otherwise insert.

        Args:
            table_name: Name of the table
            entity: The entity to save

        Returns:
            True if updated existing record
            int (record ID) if newly created
            False if error occurred
        """
        try:
            table = self.dal[table_name]

            record = {
                'name': entity.name,
                'uuid': entity.uuid,
                'config': entity.config,
                **entity.fields
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

            # Insert new document and return the ID
            with self.transaction():
                new_id = table.insert(**record)
            self.logger.debug(f"Upserted record {record} to table {table_name}")
            return new_id
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
            self.logger.info(f"Closed {self.name} database connection")