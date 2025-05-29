import logging
import traceback

from src.script.application.context import ApplicationContext
from src.script.common.constants import EntityType


def main():
    """Application entry point."""
    try:        
        # Create and initialize application context
        app_context = ApplicationContext()
        
        if app_context.initialize():
            # Get CLI API and start it
            cli = app_context.get_registry(EntityType.API).get_by_name('cli')
            if cli:
                # Start the persistent CLI session
                cli.start()
            else:
                logging.error("CLI API not found")
                return

    except Exception as e:
        logging.error(f"Error in main: {e}")
        traceback.print_exc()

if __name__ == '__main__':
    main()