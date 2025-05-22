import argparse
import shlex
from typing import Any, Dict, List, Optional

from src.script.api._ui import InputValidator, UserInterface
from src.script.constants import EntityType
from src.script.entity._api import Api

REGISTRY_COMMANDS = {
    EntityType.PROJECT: {
        'help': 'Commands for project registry',
        'commands': [
            {
                'name': 'create',
                'help': 'Create a new project',
                'handler': '_handle_project_create'
            },
            {
                'name': 'rename',
                'help': 'Rename a project',
                'args': [
                    {'name': f'--{EntityType.PROJECT}', 'short': '-p', 'help': 'Project to rename'}
                ],
                'handler': '_handle_project_rename'
            },
            {
                'name': 'delete',
                'help': 'Delete one or more project(s)',
                'args': [
                    {
                        'group': 'mutually_exclusive',
                        'required': True,
                        'args': [
                            {'name': f'--{EntityType.PROJECT}', 'short': '-p', 'help': 'Project to delete'},
                            {'name': f'--{EntityType.PROJECT}s', 'nargs': '+', 'help': 'List of projects to delete'},
                            {'name': '--all', 'action': 'store_true', 'help': 'Delete all projects'}
                        ]
                    }
                ]
            },
            {
                'name': 'add_integration',
                'help': 'Add an integration to one or more project(s)',
                'args': [
                    {'name': '--integration', 'short': '-i', 'required': True, 'help': 'Integration to add'},
                    {
                        'group': 'mutually_exclusive',
                        'required': True,
                        'args': [
                            {'name': f'--{EntityType.PROJECT}', 'short': '-p', 'help': 'Project to add integration to'},
                            {'name': f'--{EntityType.PROJECT}s', 'nargs': '+', 'help': 'List of projects to add integration to'},
                            {'name': '--all', 'action': 'store_true', 'help': 'Add to all projects'}
                        ]
                    }
                ]
            },
            {
                'name': 'remove_integration',
                'help': 'Remove an integration from one or more project',
                'args': [
                    {'name': '--integration', 'short': '-i', 'required': True, 'help': 'Integration to remove'},
                    {
                        'group': 'mutually_exclusive',
                        'required': True,
                        'args': [
                            {'name': f'--{EntityType.PROJECT}', 'short': '-p', 'help': 'Project to remove integration from'},
                            {'name': f'--{EntityType.PROJECT}s', 'nargs': '+', 'help': 'List of projects to remove integration from'},
                            {'name': '--all', 'action': 'store_true', 'help': 'Remove from all projects'}
                        ]
                    }
                ]
            },
            {
                'name': 'list',
                'help': 'List projects',
                'args': [
                    {
                        'group': 'mutually_exclusive',
                        'args': [
                            {'name': f'--{EntityType.PROJECT}', 'short': '-p', 'help': 'Project to list details for'},
                            {'name': f'--{EntityType.PROJECT}s', 'nargs': '+', 'help': 'List of projects to show details for'},
                            {'name': '--all', 'action': 'store_true', 'help': 'List all projects'}
                        ]
                    },
                    {'name': '--sort-by', 'choices': ['name', 'date', 'priority', 'status'], 'default': 'name', 'help': 'Sort by field'}
                ]
            }
        ]
    },
    EntityType.INTEGRATION: {
        'help': 'Commands for integration registry',
        'commands': [
            {
                'name': 'create',
                'help': 'Create a new integration',
                'handler': '_handle_integration_create'
            },
            {
                'name': 'rename',
                'help': 'Rename an integration',
                'args': [
                    {'name': f'--{EntityType.INTEGRATION}', 'short': '-i', 'help': 'Integration to rename'}
                ],
                'handler': '_handle_integration_rename'
            },
            {
                'name': 'delete',
                'help': 'Delete one or more integrations',
                'args': [
                    {
                        'group': 'mutually_exclusive',
                        'required': True,
                        'args': [
                            {'name': f'--{EntityType.INTEGRATION}', 'short': '-i', 'help': 'Integration to delete'},
                            {'name': f'--{EntityType.INTEGRATION}s', 'nargs': '+', 'help': 'List of integrations to delete'},
                            {'name': '--all', 'action': 'store_true', 'help': 'Delete all integrations'}
                        ]
                    }
                ]
            },
            {
                'name': 'list',
                'help': 'List integrations',
                'args': [
                    {
                        'group': 'mutually_exclusive',
                        'args': [
                            {'name': f'--{EntityType.INTEGRATION}', 'short': '-i', 'help': 'Integration to list details for'},
                            {'name': f'--{EntityType.INTEGRATION}s', 'nargs': '+', 'help': 'List of integrations to show details for'},
                            {'name': '--all', 'action': 'store_true', 'help': 'List all integrations'}
                        ]
                    },
                    {'name': '--sort-by', 'choices': ['name', 'date', 'type'], 'default': 'name', 'help': 'Sort by field'}
                ]
            }
        ]
    },
    EntityType.PROJECT_INTEGRATION: {
        'help': 'Commands for project_integration registry',
        'commands': [
            {
                'name': 'list',
                'help': 'List project integrations',
                'args': [
                    {
                        'group': 'mutually_exclusive',
                        'args': [
                            {'name': f'--{EntityType.PROJECT}', 'short': '-p', 'help': 'List integrations for specific project'},
                            {'name': f'--{EntityType.INTEGRATION}', 'short': '-i', 'help': 'List projects for specific integration'},
                            {'name': '--all', 'action': 'store_true', 'help': 'List all project integrations'}
                        ]
                    },
                    {'name': '--sort-by', 'choices': ['project', 'integration'], 'default': 'project', 'help': 'Sort by field'}
                ]
            }
        ]
    },
    EntityType.DB:{
        'help': 'Commands for database registry',
        'commands': [
            {
                'name': 'clear',
                'help': 'Clear all data from database tables',
                'args': []
            },
            {
                'name': 'list',
                'help': 'List databases',
                'args': [
                    {
                        'group': 'mutually_exclusive',
                        'args': [
                            {'name': f'--{EntityType.DB}', 'short': '-d', 'help': 'Database to list details for'},
                            {'name': f'--{EntityType.DB}s', 'nargs': '+', 'help': 'List of databases to show details for'},
                            {'name': '--all', 'action': 'store_true', 'help': 'List all integrations'}
                        ]
                    },
                    {'name': '--sort-by', 'choices': ['project', 'integration'], 'default': 'project', 'help': 'Sort by field'}
                ]
            }
        ]
    },
    'cli': {
        'help': 'CLI control commands',
        'commands': [
            {
                'name': 'exit',
                'help': 'Exit the CLI'
            },
            {
                'name': 'quit',
                'help': 'Exit the CLI (alias for exit)'
            },
            {
                'name': 'help',
                'help': 'Show available commands'
            }
        ]
    }
}

class CliUserInterface(UserInterface):
    """CLI implementation of UserInteraction."""
    
    def get_input(self, prompt: str, validators: Optional[List[InputValidator]] = [], default: Optional[str] = None) -> str:
        """
        Get input from the user via CLI with optional validation.
        
        Args:
            prompt: Prompt to display to the user
            validators: Optional InputValidators to validate the input
            
        Returns:
            str: The validated input from the user or the default value
        """
        while True:
            user_input = input(prompt + ': ').strip()
            result = self.validate(user_input, validators)

            if default is not None and not user_input:
                return default

            if not result['passed']:
                self.logger.error(result['error'])
            else:
                return user_input
    
    def confirm(self, message: str, default: bool = False) -> bool:
        """
        Ask the user for confirmation via CLI.
        
        Args:
            message: Confirmation message to display
            default: Default value if the user provides no input
            
        Returns:
            bool: True if confirmed, False otherwise
        """
        default_str = "y/N" if not default else "Y/n"
        response = input(f"{message} [{default_str}]: ").strip().lower()
        
        if not response:
            return default
            
        return response in ['y', 'yes']
    
    def display_message(self, message: str, level: str = "info") -> None:
        """
        Display a message to the user via CLI.
        
        Args:
            message: Message to display
            level: Message level (info, warning, error)
        """
        if level == "error":
            self.logger.error(message)
            print(f"ERROR: {message}")
        elif level == "warning":
            self.logger.warning(message)
            print(f"WARNING: {message}")
        else:
            self.logger.info(message)
            print(message)
    
    def display_entity_details(self, details: Dict[str, Any]) -> None:
        """
        Display entity details to the user via CLI.
        
        Args:
            entity_type: Type of entity (project, integration, etc.)
            details: Entity details to display
        """
        print(f"\n{self.entity_type.capitalize()} details:")
        for key, value in details.items():
            print(f"{key.capitalize()}: {value or '<None>'}")
    
    def display_results(self, results: Any) -> None:
        """
        Display command execution results via CLI.
        
        Args:
            results: Results from command execution
        """
        if not results:
            print("No results returned")
            return
        
        # Check if results is a dictionary with registry IDs as keys
        if isinstance(results, dict):
            for registry_name, registry_results in results.items():
                print(f"Results from {registry_name}:")
                for result in registry_results:
                    if isinstance(result, dict):
                        for key, value in result.items():
                            print(f"  {key}: {value}")
                    else:
                        print(f"  {result}")
        else:
            # Just display the result directly
            print(results)
    
    def display_list_results(self, items: List[Any], registry_type: str) -> None:
        """
        Display list results in a formatted table via CLI.
        
        Args:
            items: Items to display
            registry_type: Type of registry
        """
        if not items:
            print(f"No {registry_type} entries found")
            return
        
        # Format items as a table
        print(f"\n--- {registry_type.upper()} LIST ---")
        for item in items:
            if isinstance(item, dict):
                print(f"{item.get('name', 'Unknown')}: {item}")
            else:
                print(f"{getattr(item, 'name', 'Unknown')}: {item}")
    
    def display_help(self, parser: Any) -> None:
        """
        Display help information via CLI.
        
        Args:
            parser: ArgumentParser instance
        """
        # Display parser help
        parser.print_help()
        
        # Display special commands
        print("\nSpecial commands:")
        print("  cli exit/quit - Exit the CLI session")
        print("  cli help      - Show this help message")
        
class Cli(Api):
    """
    Command-line interface for interacting with the application.
    """
    
    def __init__(self, registry):        
        # Initialize base class
        super().__init__(registry, 'cli')
        
        # Create parser and register arguments
        self.parser = argparse.ArgumentParser(description='Luna CLI')
        self.registered_args = set()
        
        # Initialize user interface
        self._ui = CliUserInterface(self.registry.manager)
        
        # Add core arguments using subparsers for each registry
        self._setup_command_structure()
        
        # Variable to control the CLI loop
        self._running = False

    @property
    def ui(self):
        return self._ui

    @property
    def running(self):
        return self._running

    @running.setter
    def running(self, val):
        self._running = val
    
    def _setup_command_structure(self):
        """Set up the command structure with registry subparsers."""
        # Create registry subparsers
        registry_subparsers = self.parser.add_subparsers(
            dest='registry',
            help='Target registry',
            required=True
        )
        
        # Set up each registry's commands based on configuration
        for registry_name, registry_config in REGISTRY_COMMANDS.items():
            # Create registry subparser
            registry_parser = registry_subparsers.add_parser(
                registry_name, 
                help=registry_config.get('help', f"Commands for {registry_name} registry")
            )
            
            # Add commands to registry subparser
            self._setup_registry_commands(registry_parser, registry_config['commands'])
    
    def _setup_registry_commands(self, registry_parser, commands):
        """
        Set up commands for a registry.
        
        Args:
            registry_parser: ArgumentParser for the registry
            commands: List of command configurations
        """
        # Create command subparsers
        command_subparsers = registry_parser.add_subparsers(
            dest='command',
            help='Command to execute',
            required=True
        )
        
        # Add each command
        for command_config in commands:
            command_name = command_config['name']
            command_help = command_config.get('help', f"{command_name} command")
            
            # Create command parser
            command_parser = command_subparsers.add_parser(command_name, help=command_help)
            
            # Add arguments to command
            if 'args' in command_config:
                self._add_command_arguments(command_parser, command_config['args'])
    
    def _add_command_arguments(self, command_parser, args_config):
        for arg_config in args_config:
            # Handle argument groups
            if 'group' in arg_config:
                group_type = arg_config['group']
                required = arg_config.get('required', False)
                
                if group_type == 'mutually_exclusive':
                    group = command_parser.add_mutually_exclusive_group(required=required)
                    # Pass the group to add arguments, not the original parser
                    self._add_command_arguments(group, arg_config['args'])
                else:
                    self.logger.warning(f"Unknown group type: {group_type}")
            else:
                # Handle regular arguments
                arg_name = arg_config['name']
                kwargs = {k: v for k, v in arg_config.items() if k != 'name' and k != 'short'}
                
                # If there's a short version, add it to the args
                args = [arg_name]
                if 'short' in arg_config:
                    args.append(arg_config['short'])
                
                # Add argument to parser
                command_parser.add_argument(*args, **kwargs)
    
    def _add_argument_from_integration(self, parser, *args, **kwargs):
        """
        Add an argument to the parser, but only if it hasn't been added already.
        
        Args:
            parser: ArgumentParser to add the argument to
            *args: Argument names
            **kwargs: Argument configuration
                
        Returns:
            bool: True if the argument was added, False if it was already registered
        """
        # Extract argument names from args (they start with -)
        arg_names = {arg for arg in args if arg.startswith('-')}
        
        # Check if any of these argument names are already registered
        if arg_names.intersection(self.registered_args):
            # At least one of the argument names is already registered, so skip it
            return False
        
        # None of the argument names are registered yet, so add them all
        self.registered_args.update(arg_names)
        
        try:
            parser.add_argument(*args, **kwargs)
            return True
        except Exception as e:
            self.logger.warning(f"Error adding argument {args}: {e}")
            return False
    
    def start(self):
        """
        Start the persistent CLI session.
        
        """
        self.running = True
        self.ui.display_message("Starting persistent CLI session. Type 'cli exit' or 'cli quit' to exit.")
        
        # Setup readline for command history
        try:
            import atexit
            import os
            import readline
            
            # History file path
            histfile = os.path.join(os.path.expanduser("~"), ".luna_history")
            
            # Create history file if it doesn't exist
            try:
                readline.read_history_file(histfile)
                # Set history length
                readline.set_history_length(1000)
            except FileNotFoundError:
                pass
                
            # Save history on exit
            atexit.register(readline.write_history_file, histfile)
            
            self.ui.display_message("Command history enabled (use up/down arrows to navigate)")
        except (ImportError, ModuleNotFoundError):
            self.ui.display_message("Readline module not available. Command history disabled.", "warning")
        
        while self.running:
            try:
                # Display prompt and get user input
                command = input("\nLuna CLI> ").strip()
                
                # Skip empty commands
                if not command:
                    continue
                
                # Parse the command into arguments
                try:
                    # Use shlex to properly handle quoted arguments
                    args_list = shlex.split(command)
                    args = self.parser.parse_args(args_list)
                    
                    # Handle CLI control commands
                    if args.registry == 'cli':
                        if args.command in ['exit', 'quit']:
                            self.ui.display_message("Exiting CLI session.")
                            self.running = False
                            continue
                        elif args.command == 'help':
                            self.ui.display_help(self.parser)
                            continue
                    
                    # Process the command
                    self._process_command(args)
                    
                except SystemExit:
                    # Catch the SystemExit that argparse.parse_args raises on error
                    # This allows us to keep the CLI running even when there's a parsing error
                    continue
                
            except KeyboardInterrupt:
                print("\nUse 'cli exit' to quit.")
            except EOFError:
                # Handle Ctrl+D (EOF)
                print("\nExiting CLI session.")
                self.running = False
            except Exception as e:
                self.ui.display_message(f"Error processing command: {e}", "error")
                import traceback
                traceback.print_exc()
    
    def _process_command(self, args):
        """
        Process a command based on parsed arguments.
        
        Args:
            args: The parsed command line arguments
        """
        registry = args.registry
        command = args.command

        self.logger.debug(f"Processing command: {registry} {command} with args: {vars(args)}")
        
        # Find special handler method if defined in config
        handler_method = None
        for cmd_config in REGISTRY_COMMANDS.get(registry, {}).get('commands', []):
            if cmd_config.get('name') == command and 'handler' in cmd_config:
                handler_method = cmd_config['handler']
                break
        
        if handler_method and hasattr(self, handler_method):
            # Call the handler method
            handler = getattr(self, handler_method)
            result = handler(args)
            return result
        
        # Dispatch command to appropriate registry
        params = vars(args)
        del params['registry']
        del params['command']
        result = self.dispatch_command(registry, command, params)
        
        # Display results
        if command == 'list':
            self.ui.display_list_results(result, registry)
        else:
            self.ui.display_results(result)
    
    def _handle_project_create(self, args):
        """
        Handle project creation.
        
        Args:
            args: Command line arguments
            
        Returns:
            Any: Creation result
        """

        self.ui.set_context({'entity_type': EntityType.PROJECT})

        # Get name, emoji, title
        name = self.ui.get_input("Enter project name", self.ui.new_entity_validators)
        emoji = self.ui.get_input("Enter an emoji prefix (or press enter to leave empty)", self.ui.emoji_validators, '')
        title = self.ui.format_kebabcase_to_titlecase(name)
        
        # Display details for confirmation
        params = {
            'name': name,
            'title': title,
            'emoji': emoji
        }
        self.ui.display_entity_details(params)
        
        # Confirm details
        if not self.ui.confirm("\nConfirm these details?"):
            self.ui.display_message("Operation cancelled", "info")
            return None
        
        result = self.dispatch_command(EntityType.PROJECT, 'create', params)
        
        if result:
            self.ui.display_message(f"Created project {result.name}", "info")
        else:
            self.ui.display_message("Failed to create project", "error")
        
        return result
    
    def _handle_project_rename(self, args):
        """
        Handle project rename.
        
        Args:
            args: Command line arguments
            
        Returns:
            Any: Rename result
        """

        self.ui.set_context({'entity_type': EntityType.PROJECT})
        
        # Get project name

        project_name = self.ui.get_input("Enter name of project to rename", self.ui.existing_entity_validators)

        project_registry = self.registry.manager.get_by_name(EntityType.PROJECT)
        project = project_registry.get_by_name(project_name)

        new_name = self.ui.get_input("Enter new name: ", self.ui.new_entity_validators)
        new_emoji = self.ui.get_input(f"Enter new emoji prefix (or press enter to use existing emoji {project.emoji})", self.ui.emoji_validators, project.emoji)
        new_title = self.ui.format_kebabcase_to_titlecase(new_name)
                                
        # Confirm changes
        params = {
            'project': project_name,
            'new_name': new_name,
            'new_title': new_title,
            'new_emoji': new_emoji
        } 
        self.ui.display_entity_details(params)
        
        if not self.ui.confirm("\nConfirm these changes?"):
            self.ui.display_message("Operation cancelled", "info")
            return None
        
        result = self.dispatch_command(EntityType.PROJECT, 'rename', params)
        
        if result:
            self.ui.display_message(f"Updated project '{project_name}'", "info")
            self.ui.display_message(f"  Name changed to: {result.name}", "info")
            self.ui.display_message(f"  Title changed to: {result.title}", "info")
            self.ui.display_message(f"  Emoji changed to: {result.emoji or 'None'}", "info")
        else:
            self.ui.display_message("Failed to rename project", "error")
        
        return result
    
    def _handle_integration_create(self, args):
        """
        Handle integration creation.
        
        Args:
            args: Command line arguments
            
        Returns:
            Any: Creation result
        """        

        self.ui.set_context({'entity_type': EntityType.INTEGRATION})

        # Get integration name
        name = self.ui.get_input("Enter integration name", self.ui.new_entity_validators)
        emoji = self.ui.get_emoji("Enter an emoji prefix (or press enter to leave empty)", self.ui.emoji_validators, '')
        type = self.ui.get_input("Enter integration type", self.ui.existing_entity_validators)

        # Display details for confirmation
        params = {
            'name': name,
            'emoji': emoji,
            'type': type
        }
        self.ui.display_entity_details(params)
        
        # Confirm details
        if not self.ui.confirm("\nConfirm these details?"):
            self.ui.display_message("Operation cancelled", "info")
            return None

        result = self.dispatch_command(EntityType.INTEGRATION, 'create', params)
        
        if result:
            self.ui.display_message(f"Created integration: {result.get('name', name)}", "info")
        else:
            self.ui.display_message("Failed to create integration", "error")
        
        return result
    
    def _handle_integration_rename(self, args):
        """
        Handle integration rename.
        
        Args:
            args: Command line arguments
            
        Returns:
            Any: Rename result
        """
        self.ui.set_context({'entity_type': EntityType.INTEGRATION})

        integration_name = self.ui.get_input("Enter name of integration to rename", self.ui.existing_entity_validators)

        integration_registry = self.registry.manager.get_by_name(EntityType.INTEGRATION)
        integration = integration_registry.get_by_name(integration_name)

        new_name = self.ui.get_input("Enter new name", self.ui.new_entity_validators)
        new_emoji = self.ui.get_input(f"Enter new emoji prefix (or press enter to use existing emoji {integration.emoji})", self.ui.emoji_validators, integration.emoji)
        new_title = self.ui.format_kebabcase_to_titlecase(new_name)

        
        params = {
            'integration': integration_name,
            'new_name': new_name,
            'new_title': new_title,
            'new_emoji': new_emoji
        }
        
        self.ui.display_entity_details("integration", params)
        
        if not self.ui.confirm("\nConfirm these changes?"):
            self.ui.display_message("Operation cancelled", "info")
            return None

        result = self.dispatch_command(EntityType.INTEGRATION, 'create', params)
                
        if result:
            self.ui.display_message(f"Updated project '{integration_name}'", "info")
            self.ui.display_message(f"  Name changed to: {result.name}", "info")
            self.ui.display_message(f"  Title changed to: {result.title}", "info")
            self.ui.display_message(f"  Emoji changed to: {result.emoji or 'None'}", "info")
        else:
            self.ui.display_message("Failed to rename integration", "error")
        
        return result