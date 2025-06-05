import click

from api.cli.base import SubparserBase
from common.enums import CommandType
from entities.database.interface import DatabaseInterface


class DatabaseSubparserBase(SubparserBase, DatabaseInterface):
    def __init__(self, ctx):
        super().__init__(ctx)

    @click.command(CommandType.CLEAR.value)
    @click.option('--yes', '-y', is_flag=True, help='Skip confirmation prompt')
    def clear(self, yes: bool):
        """Clear active database"""
        self.logger.info(f"Clearing database")

        try:
            if not yes:
                click.echo(f"This will clear all data from the database")
                if not click.confirm("\nAre you sure you want to continue?"):
                    click.echo("Cancelled")
                    self.logger.info(f"Database clear cancelled by user")
                    return
                click.echo(f"✓ Database connection is working")
                self.logger.info(f"Database cleared successfully")
        except ValueError as e:
            self.logger.error(f"Database not found: {e}")
            click.echo(f"Error: {e}", err=True)
            raise click.ClickException(str(e))
        except Exception as e:
            self.logger.error(f"Error testing database connection: {e}", exc_info=True)
            click.echo(f"Error: {e}", err=True)
            raise click.ClickException("Failed to tests database connection")

    @click.command(CommandType.TEST.value)
    def test(self):
        """Test active database"""
        self.logger.info(f"Testing database connection")

        try:
            database = self.service.get_active_db()
            if not database:
                return

            if self.service.test(database):
                click.echo(f"✓ Database connection is working")
                self.logger.info(f"Database connection tests successful")
            else:
                click.echo(f"✗ Database connection failed", err=True)
                self.logger.error(f"Database connection tests failed")
                raise click.ClickException("Connection tests failed")

        except ValueError as e:
            self.logger.error(f"Database not found: {e}")
            click.echo(f"Error: {e}", err=True)
            raise click.ClickException(str(e))
        except Exception as e:
            self.logger.error(f"Error testing database connection: {e}", exc_info=True)
            click.echo(f"Error: {e}", err=True)
            raise click.ClickException("Failed to tests database connection")
