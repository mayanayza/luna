import subprocess

from script.src.config import Config
from script.src.utils import setup_logging


class ThingsHandler:

    def __init__(self, config: Config):
        self.config = config
        self.logger = setup_logging(__name__)

    def create(self, display_name: str) -> None:
            """Create a project in Things 3 via AppleScript. Raises if creation fails."""
            if not self.config.enable_things3:
                return

            applescript = f'''
            tell application "Things3"
                set newProject to make new project with properties {{{{name:"{display_name}"}}}}
                set newProject's area to area "🎨 Art"
            end tell
            '''
            try:
                subprocess.run(['osascript', '-e', applescript], check=True)
                self.logger.info(f"Created Things 3 project: {display_name}")
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Failed to create Things 3 project: {e}")

    def rename(self, old_display_name: str, new_display_name: str) -> None:
        """Rename a project in Things 3"""
        if not self.config.enable_things3:
            return

        applescript = f'''
        tell application "Things3"
            set oldProject to first project whose name = "{old_display_name}"
            set oldProject's name to "{new_display_name}"
        end tell
        '''
        try:
            subprocess.run(['osascript', '-e', applescript], check=True)
            self.logger.info(f"Renamed Things 3 project from '{old_display_name}' to '{new_display_name}'")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to rename Things 3 project: {e}")
