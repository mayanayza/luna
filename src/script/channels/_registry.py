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
        """
        Execute a command on specified channels and projects
        
        Args:
            command: The command to execute (e.g., 'publish', 'stage', 'create', 'list')
            channels: List of channel names to execute the command on
            projects: List of project names to apply the command to
            all_projects: If True, apply to all projects
            all_channels: If True, apply to all channels
            **kwargs: Additional arguments specific to the command
        """
        # Get all available channels
        all_c = self._channels.keys()
        
        # Determine which channels to use
        if all_channels:
            channels = list(all_c)
        elif not channels:
            raise ValueError("No channels specified. Use --channels or -ch.")
        else:
            invalid_channels = set(channels) - set(all_c)
            if invalid_channels:
                raise ValueError(f"Invalid channels specified: {invalid_channels}")
        
        # Check if command requires projects
        project_required_commands = ['publish', 'stage', 'init', 'delete']
        project_optional_commands = []  # Commands where projects are optional
        project_ignored_commands = ['create', 'list']  # Commands that don't need projects
        
        # For commands that require or use projects, validate them
        if command in project_required_commands or command in project_optional_commands:
            all_p = []
            for item in self.config.base_dir.iterdir():
                if is_project(self, item):
                    all_p.append(item.name)
                    
            if all_projects:
                projects = all_p
            elif not projects and command in project_required_commands:
                raise ValueError(f"Command '{command}' requires projects. Use --projects or -p.")
            elif projects:
                invalid_projects = set(projects) - set(all_p)
                if invalid_projects:
                    raise ValueError(f"Invalid projects specified: {invalid_projects}")
        
        # Prepare context for executing the command
        command_context = {
            **kwargs,
            'projects': projects if command not in project_ignored_commands else None
        }
        
        # Execute command on specified channels
        executed = False
        for channel in channels:
            if command in self._channels[channel]:
                self.logger.info(f"Executing '{command}' on channel '{channel}'")
                self._channels[channel][command](**command_context)
                executed = True
            else:
                self.logger.info(f"Channel '{channel}' does not support command '{command}'")
        
        if not executed:
            self.logger.warning(f"Command '{command}' was not executed on any channel.")