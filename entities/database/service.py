from entities.database.interface import DatabaseInterface
from services.base import Service


class DatabaseServiceBase(DatabaseInterface, Service):
    """Service for database operations"""

    def clear(self):
        try:
            active_db = self.registry.get_active_db()
            if active_db is not None:
                active_db.clear()
        except Exception as e:
                raise RuntimeError(f"Failed to clear database: {e}")

    def test(self):
        try:
            active_db = self.registry.get_active_db()
            if active_db is not None:
                active_db.dal.executesql("SELECT 1")
        except Exception as e:
            raise RuntimeError(f"Failed to test database connection: {e}")

    # def clear_database(self, database: Database) -> bool:
    #     """Clear all data from database"""
    #     try:
    #         return database.clear()
    #     except Exception as e:
    #         raise RuntimeError(f"Failed to clear database {database.name}: {e}")
    #
    # def test_connection(self, database: Database) -> bool:
    #     """Test database connection"""
    #     try:
    #         if not database.dal:
    #             return False
    #         # Simple tests query
    #         database.dal.execute_sql("SELECT 1")
    #         return True
    #     except Exception as e:
    #         self.logger.error(f"Database connection tests failed: {e}")
    #         return False

