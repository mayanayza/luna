import argparse
import shlex
from typing import Any, Dict

from src.script.api._form import CliFormBuilder
from src.script.api._ui import UserInterface
from src.script.constants import Command, EntityType
from src.script.entity._api import Api
from src.script.entity._base import CreatableEntity

REGISTRY_COMMANDS = {
    EntityType.PROJECT: {
        'help': 'Commands for project registry',
        'commands': [
            {
                'name': 'create',
                'help': 'Create a new project',
                'handler': 'handle_entity_create'
            },
            {
                'name': 'rename',
                'help': 'Rename a project',
                'handler': 'handle_entity_rename'
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
                'name': 'detail',
                'help': 'Show details of a project',
                'args': [
                    {'name': f'--{EntityType.PROJECT}', 'short': '-p', 'required': True, 'help': 'Project to show details for'},
                ]
            },
            {
                'name': 'list',
                'help': 'List projects',
                'args': [
                    {
                        'group': 'mutually_exclusive',
                        'args': [
                            {'name': f'--{EntityType.PROJECT}', 'short': '-p', 'help': 'Project to list summary for'},
                            {'name': f'--{EntityType.PROJECT}s', 'nargs': '+', 'help': 'List of projects to show summary for'},
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
                'help': 'Create a new instance of an integration',
                'handler': '_handle_integration_create'
            },
            {
                'name': 'rename',
                'help': 'Rename an integration',
                'handler': 'handle_entity_rename'
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
                'name': 'detail',
                'help': 'Show details of an integration',
                'args': [
                    {'name': f'--{EntityType.INTEGRATION}', 'short': '-i', 'required': True, 'help': 'Integration to show details for'},
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
            },
            {
                'name': 'edit',
                'help': 'Edit integration configuration',
                'handler': '_handle_integration_edit'
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
            },
            {
                'name': 'detail',
                'help': 'Show details of a project integration',
                'args': [
                    {'name': f'--{EntityType.PROJECT_INTEGRATION}', 'short': '-pi', 'required': True, 'help': 'Project integration to show details for'},
                ]
            },
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
                'name': 'detail',
                'help': 'Show details of a database',
                'args': [
                    {'name': f'--{EntityType.DB}', 'short': '-db', 'required': True, 'help': 'Database to show details for'},
                ]
            },
            {
                'name': 'list',
                'help': 'List databases',
                'args': [
                    {
                        'group': 'mutually_exclusive',
                        'args': [
                            {'name': f'--{EntityType.DB}', 'short': '-db', 'help': 'Database to list details for'},
                            {'name': f'--{EntityType.DB}s', 'nargs': '+', 'help': 'List of databases to show details for'},
                            {'name': '--all', 'action': 'store_true', 'help': 'List all integrations'}
                        ]
                    },
                    {'name': '--sort-by', 'choices': ['name'], 'default': 'name', 'help': 'Sort by field'}
                ]
            }
        ]
    },
    EntityType.HANDLER:{
        'help': 'Commands for handler registry',
        'commands': [
            {
                'name': 'list',
                'help': 'List handlers',
                'args': [
                    {
                        'group': 'mutually_exclusive',
                        'args': [
                            {'name': f'--{EntityType.HANDLER}', 'short': '-db', 'help': 'Handler to list details for'},
                            {'name': f'--{EntityType.HANDLER}s', 'nargs': '+', 'help': 'List of handlers to show details for'},
                            {'name': '--all', 'action': 'store_true', 'help': 'List all handlers'}
                        ]
                    },
                    {'name': '--sort-by', 'choices': ['name'], 'default': 'name', 'help': 'Sort by field'}
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
    """Simplified CLI UserInterface - focused on display-only operations"""
    
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
    
    def respond(self, message: str, level: str = "info") -> None:
        """
        Display a message to the user via CLI.
        
        Args:
            message: Message to display
            level: Message level (info, warning, error)
        """
        getattr(self.logger, level)(message)
    
    def display_key_values_list(self, details: Dict[str, Any]) -> None:
        """
        Display a list of keys and values to the user via CLI.
        
        Args:
            details: Entity details to display
        """
        for key, value in details.items():
            print(f"{key.capitalize()}: {value or '<None>'}")
    
    def display_results(self, results: Any) -> None:
        """
        Display command execution results via CLI.
        
        Args:
            results: Results from command execution
        """
        # Check if results is a dictionary with registry IDs as keys
        if isinstance(results, dict):
            for result in results:
                if isinstance(result, dict):
                    for key, value in result.items():
                        print(f"  {key}: {value}")
                else:
                    print(f"  {result}")
        else:
            # Just display the result directly
            print(results)
    
    def display_results_tabular(self, results, headers):
        from tabulate import tabulate

        tabular = []

        for result in results:
            tab = []
            for header in headers:
                if header in result:
                    tab.append(result[header])
                else:
                    tab.append('')
            tabular.append(tab)

        print(tabulate(tabular, headers))
    
    def help(self, parser: Any) -> None:
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
        self._ui = CliUserInterface(self.registry.manager, CliFormBuilder)
        
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
    
    def start(self):
        """
        Start the persistent CLI session.
        
        """
        self.running = True
        self.ui.respond("Starting persistent CLI session. Type 'cli exit' or 'cli quit' to exit.")
        
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
            
            self.ui.respond("Command history enabled (use up/down arrows to navigate)")
        except (ImportError, ModuleNotFoundError):
            self.ui.respond("Readline module not available. Command history disabled.", "warning")
        
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
                            self.ui.respond("Exiting CLI session.")
                            self.running = False
                            continue
                        elif args.command == 'help':
                            self.ui.help(self.parser)
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
                self.ui.respond(f"Error processing command: {e}", "error")
                import traceback
                traceback.print_exc()
    
    def _process_command(self, args):
        """
        Process a command based on parsed arguments.
        
        Args:
            args: The parsed command line arguments
        """
        registry_name = args.registry
        command = args.command

        self.ui.context.entity_type = registry_name

        self.logger.debug(f"Processing command: {registry_name} {command} with args: {vars(args)}")
        
        # Find special handler method if defined in config
        handler_method = None
        for cmd_config in REGISTRY_COMMANDS.get(registry_name, {}).get('commands', []):
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
        results = self.dispatch_command(registry_name, command, params)

        if isinstance(results, list):
            results = [r for r in results if r is not None]
        
        # Display results
        print(f"\n--- {registry_name.upper()} {command.upper()} RESULTS ---")
        if not results:
            print("No results returned")

        if results:
            if command == 'list':
                self.ui.display_results_tabular(results, results[0].keys())
            elif command == 'detail':
                self.ui.display_key_values_list(results[0])
            else:
                for result in results:
                    self.ui.display_results(result)
    
    def _handle_integration_create(self, args):
        """
        Handle integration creation using streamlined form-based approach.
        
        Args:
            args: Command line arguments
            
        Returns:
            Any: Creation result
        """
        # Get integration type selection first (simple selection, not a form field)
        types = self.ui.context.current_entity_registry.get_integration_filenames()
        integration_type = self.ui.form_builder.get_selection(
            "Select integration type:", 
            types
        )
        
        if not integration_type:
            return None
        
        # Create and fill the integration creation form with prefix
        name_prefix = f"{integration_type}-"
        form_data = CreatableEntity.create_form(self.ui, EntityType.INTEGRATION, name_prefix=name_prefix)
        if not form_data:
            return None
        
        # Extract values and build final name with prefix
        base_name = form_data["name"]
        emoji = form_data["emoji"]
        
        # Build prefixed name
        name = f"{name_prefix}{base_name}"
        title = self.ui.validator.format_kebabcase_to_titlecase(name)
        
        # Create integration
        params = {
            'integration_type': integration_type,
            'name': name,
            'emoji': emoji,
            'title': title
        }
        
        integration = self.dispatch_command(EntityType.INTEGRATION, Command.CREATE, params)
        
        self.handle_entity_edit(integration)

        return integration

    
    