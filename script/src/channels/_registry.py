from typing import Callable, Dict, List, Optional

from script.src.config import Config
from script.src.constants import Files
from script.src.utils import setup_logging


class ChannelRegistry:
    def __init__(self, config: Config):
        self.config = config
        self.logger = setup_logging(__name__)
        self._channels: Dict[str, Callable] = {}

    def register(self, output_name: str, publish_func: Callable):
        self._channels[output_name] = publish_func
    
    def publish(self, 
                channels: Optional[List[str]] = None, 
                projects: Optional[List[str]] = None, 
                all_projects: Optional[bool] = False,
                all_channels: Optional[bool] = False,
                **kwargs):

        all_projects = []
        for item in self.config.base_dir.iterdir():
            if item.is_dir() and (item / Files.METADATA).exists():
                all_projects.append(item.name)

        if all_channels:
            channels = list(self._channels.keys())
        elif not channels:
            raise ValueError("No channels specified. Use --channels or -ch.")
        else:
            invalid_channels = set(channels) - set(self._channels.keys())
            if invalid_channels:
                raise ValueError(f"Invalid channels specified: {invalid_channels}")

        if all_projects:
            projects = all_projects
        elif not projects:
            raise ValueError("No projects specified. Use --projects or -p.")
        else:
            invalid_projects = set(projects) - set(all_projects)
            if invalid_projects:
                raise ValueError(f"Invalid projects specified: {invalid_projects}")        

        # Prepare context for publication
        publish_context = {
            **kwargs,
            'projects': projects
        }
        
        # Publish to specified channels
        for channel in channels:
            self._channels[channel](**publish_context)