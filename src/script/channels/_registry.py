from typing import Callable, Dict, List, Optional

from src.script.config import Config
from src.script.utils import is_project, setup_logging


class ChannelRegistry:
    def __init__(self, config: Config):
        self.config = config
        self.logger = setup_logging(__name__)
        self._channels = {}

    def register(self, channel: str, funcs: Dict[str, Callable]):
       self._channels[channel] = {}
       for command, func in funcs.items():
           self._channels[channel][command] = func

    
    def command(self, 
                command: str,
                channels: Optional[List[str]] = None, 
                projects: Optional[List[str]] = None, 
                all_projects: Optional[bool] = False,
                all_channels: Optional[bool] = False,
                **kwargs):

        all_c = self._channels.keys()
        if all_channels:
            channels = list(all_c)
        elif not channels:
            raise ValueError("No channels specified. Use --channels or -ch.")
        else:
            invalid_channels = set(channels) - set(all_c)
            if invalid_channels:
                raise ValueError(f"Invalid channels specified: {invalid_channels}")


        all_p = []
        for item in self.config.base_dir.iterdir():
            if is_project(self, item):
                all_p.append(item.name)
        if all_projects:
            projects = all_p
        elif not projects:
            raise ValueError("No projects specified. Use --projects or -p.")
        else:
            invalid_projects = set(projects) - set(all_p)
            if invalid_projects:
                raise ValueError(f"Invalid projects specified: {invalid_projects}")        

        # Prepare context for publication
        publish_context = {
            **kwargs,
            'projects': projects
        }
        
        # Publish to specified channels
        for channel in channels:
            if self._channels[channel][command]:
                self._channels[channel][command](**publish_context)
            else:
                self.logger.info(f"{channel} does not support comand '{command}'")