import logging
import traceback

from src.script.api.cli.main import cli
from src.script.application.context import ApplicationContext


def main():
    """Application entry point."""
    try:        
        # Create and initialize application context
        app_context = ApplicationContext()
        
        if app_context.initialize():
            if cli:
                # Start the persistent CLI session
                cli(obj={'app_context': app_context})
            else:
                logging.error("CLI API not found")
                return

    except Exception as e:
        logging.error(f"Error in main: {e}")
        traceback.print_exc()

if __name__ == '__main__':
    main()