import os
from pathlib import Path

from jinja2 import Environment, FileSystemLoader


class TemplateProcessor:
    def __init__(self):
        current_dir = Path(__file__).parent
        # self.logger = setup_logging(__name__)
        self.env = Environment(
            loader=FileSystemLoader(current_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        
        def basename(path):
            return os.path.basename(path)

        self.env.filters['basename'] = basename