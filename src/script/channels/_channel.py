from src.script.config import Config
from src.script.templates.processor import TemplateProcessor
from src.script.utils import setup_logging


class Channel:
    def __init__(self, name, class_name, config: Config) -> None:
        self.config = config
        self.class_name = class_name
        self.tp = TemplateProcessor(config)
        self.logger = setup_logging(name)
        self.media = {}