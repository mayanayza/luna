import argparse
import logging
import shlex
from typing import Any, Dict, List, Optional

from src.script.api._input_converter import ApiInputConverter
from src.script.common.constants import CommandType, EntityType
from src.script.entity.api import Api
from src.script.entity.handler import Handler
from src.script.input.factory import InputFactory
from src.script.input.input import Input, InputField, InputGroup


class CliUserInterface:
    """CLI user interface - handles display operations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def confirm(self, message: str, default: bool = False) -> bool:
        default_str = "y/N" if not default else "Y/n"
        response = input(f"{message} [{default_str}]: ").strip().lower()
        
        if not response:
            return default
            
        return response in ['y', 'yes']
    
    def respond(self, message: str, level: str = "info") -> None:
        getattr(self.logger, level)(message)
    
    def display_key_values_list(self, details: Dict[str, Any]) -> None:
        import json
        print(json.dumps(details, indent=4))
    
    def display_results(self, results: Any) -> None:
        if isinstance(results, dict):
            for result in results:
                if isinstance(result, dict):
                    for key, value in result.items():
                        print(f"  {key}: {value}")
                else:
                    print(f"  {result}")
        else:
            print(results)
    
    def display_results_tabular(self, results, headers):
        try:
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
        except ImportError:
            # Fallback if tabulate not available
            for result in results:
                self.display_results(result)
    
    def display_validation_errors(self, validation_errors: Dict[str, Any]) -> None:
        """Display validation errors in a user-friendly format"""
        print("\nValidation Errors:")
        for field_name, error in validation_errors.items():
            if isinstance(error, dict):
                message = error.get('message', 'Unknown validation error')
                code = error.get('code', '')
                print(f"  • {field_name}: {message}")
                if code:
                    print(f"    (Error code: {code})")
            else:
                print(f"  • {field_name}: {error}")
        print()
    
    def help(self, parser: Any) -> None:
        parser.print_help()
        
        print("\nSpecial commands:")
        print("  cli exit/quit - Exit the CLI session")
        print("  cli help      - Show this help message")


class Cli(Api):
    """Command-line interface that dynamically builds from entity interfaces"""
    
    def __init__(self, registry, **kwargs):
        super().__init__(registry, 'cli', **kwargs)
        
        # Single CLI converter handles both conversion and input collection
        self._cli_converter = CliInputConverter()
        self._user_interface = CliUserInterface()
        
        # Parser will be built dynamically
        self.parser = None
        self._running = False
    
    @property
    def user_interface(self):
        return self._user_interface

    @property
    def cli_converter(self):
        return self._cli_converter
    
    def start(self):
        """Start the CLI session"""
        self._build_parser_from_handler_registry()
        self._running = True
        
        print("Starting CLI session. Type 'cli exit' to quit.\n")
        self._setup_readline()
        
        while self._running:
            try:
                command = input("Luna CLI> ").strip()
                if not command:
                    continue
                
                self._execute_command(command)
                    
            except KeyboardInterrupt:
                print("\nUse 'cli exit' to quit.")
            except EOFError:
                print("\nExiting CLI session.")
                self._running = False

    def _build_parser_from_handler_registry(self):
        """Build the argparse structure from entity interfaces"""
        
        # Create a fresh parser each time
        self.parser = argparse.ArgumentParser(description='Luna CLI')
        
        # Create entity type subparsers
        entity_type_subparsers = self.parser.add_subparsers(
            dest='entity_type',
            help='Target entity type',
            required=True
        )
        
        # Add CLI control commands
        self._add_cli_control_commands(entity_type_subparsers)

        command_handlers_by_entity_type = {}

        for command_handler in self.handler_registry.get_all_entities():
            if isinstance(command_handler, Handler):
                entity_type = command_handler.entity_type
                if command_handler.entity_type not in command_handlers_by_entity_type:
                    command_handlers_by_entity_type[entity_type] = []
                command_handlers_by_entity_type[entity_type].append(command_handler)

        for entity_type, handlers in command_handlers_by_entity_type.items():
            self._build_entity_type_parser(entity_type_subparsers, entity_type, handlers)

    def _build_entity_type_parser(self, entity_type_subparsers, entity_type, command_handlers):
        """Build parser for a specific entity type"""

        # Create entity type parser
        entity_parser = entity_type_subparsers.add_parser(
            entity_type.value,
            help=f"Commands for {entity_type.value}"
        )
        
        # Create command subparsers
        command_type_subparsers = entity_parser.add_subparsers(
            dest='command_type',
            help='Command to execute',
            required=True
        )

        for command_handler in command_handlers:
            self._add_input_as_command(command_type_subparsers, command_handler.command_type.value, command_handler.input_obj)
        
    def _add_input_as_command(self, command_subparsers, command_type: str, input_obj):
        """Add an input as a CLI command"""
        if input_obj:
            cli_spec = self.cli_converter.to_api_spec(input_obj)
            
            # Create command parser
            cmd_parser = command_subparsers.add_parser(
                command_type,
                help=cli_spec.get('help', f"Execute {command_type}")
            )
            
            # Add arguments from CLI spec
            self._add_arguments_from_spec(cmd_parser, cli_spec.get('args', []))

    def _add_arguments_from_spec(self, parser, args_spec: List[Dict[str, Any]]):
        """Add arguments to parser from CLI specification"""
        
        for arg_spec in args_spec:
            try:
                # Regular argument
                arg_names = [arg_spec['name']]
                if 'short' in arg_spec:
                    arg_names.append(arg_spec['short'])
                
                # Filter out metadata keys
                kwargs = {k: v for k, v in arg_spec.items() 
                         if k not in ['name', 'short']}
                                    
                parser.add_argument(*arg_names, **kwargs)
                    
            except Exception as e:
                self.logger.error(f"Error adding argument {arg_spec}: {e}")

    def _execute_command(self, command: str):
        """Parse and execute a command"""
        try:
            args = self.parser.parse_args(shlex.split(command))
            
            if args.entity_type == 'cli':
                self._handle_cli_command(args)
            else:
                command_success = self._process_entity_command(args)
                
                # Rebuild parser after successful command execution
                if command_success:
                    self._build_parser_from_handler_registry()
                
        except SystemExit:
            # argparse error - continue
            pass

    def _process_entity_command(self, args) -> bool:
        """Process a command for an entity type and return success status"""
        entity_type_enum = EntityType(args.entity_type)
        command_type_enum = CommandType(args.command_type)
        handler = self.handler_registry.get_handler_by_entity_and_command_types(entity_type_enum, command_type_enum)

        params = {k: v for k, v in vars(args).items() 
                 if not k.startswith('_') and k not in ['entity_type', 'command_type']}

        input_obj = handler.input_obj

        print(f"Initial params: {params}")

        if not handler.needs_target:
            # Registry-level commands (like list, create)
            return self._convert_and_execute(
                input_obj,
                args.command_type, 
                params,
                {
                    "interface": "cli", 
                    "authenticated": True,
                }
            )
        else:

            input_obj.prepend_child(
                InputFactory.entity_target_selector_field(
                    registry=input_obj.handler_registry.manager.get_by_entity_type(entity_type_enum),
                    handler_registry=input_obj.handler_registry
                ))

            return self._convert_and_execute(
                input_obj,
                args.command_type, 
                params,
                {
                    "interface": "cli", 
                    "authenticated": True,
                }
            )
    
    def _convert_and_execute(self, input_obj, command_type, params, context) -> bool:
        """Convert and execute command, return success status"""
        try:
            result = self.cli_converter.execute_with_input_collection(
                input_obj,
                command_type, 
                params,
                context
            )

            command_output = []
            
            # Display results based on success/failure
            if result.get("success"):
                
                for handler_result in result.handler_results:

                    if hasattr(handler_result, 'success'):
                        if handler_result.success:
                            self.display_results(command_type, handler_result.result)                            
                            command_output.append(handler_result.result)
                        else:
                            # Handler execution failed
                            error = handler_result.error
                            self.logger.error(f"Command '{command_type}' {error['type']} handler execution failed: {error.error}")                                
                            command_output.append(error)

                return command_output

            else:
                # Handle different types of errors more specifically
                if result.get("validation_errors"):
                    self.logger.error(f"Command '{command_type}' failed due to validation errors:")
                    self.user_interface.display_validation_errors(result["validation_errors"])
                elif result.get("cancelled"):
                    self.logger.warning(f"Command '{command_type}' was cancelled by user.")
                elif result.get("error"):
                    self.logger.error(f"Command '{command_type}' failed: {result['error']}")
                else:
                    self.logger.error(f"Command '{command_type}' failed for unknown reason.")
                    print(f"Full result: {result}")
                
                return False  # Command failed
            
        except Exception as e:
            self.logger.error(f"Error executing {command_type}: {e}", exc_info=True)
            return False  # Command failed due to exception

    def _handle_cli_command(self, args):
        """Handle CLI control commands"""
        if args.command in ['exit', 'quit']:
            self._running = False
            print("Exiting CLI session.")
        elif args.command == 'help':
            self.user_interface.help(self.parser)
        
    def _add_cli_control_commands(self, entity_type_subparser):
        """Add CLI-specific control commands"""
        cli_parser = entity_type_subparser.add_parser(
            'cli',
            help='CLI control commands'
        )
        
        cli_commands = cli_parser.add_subparsers(
            dest='command',
            help='CLI command',
            required=True
        )
        
        cli_commands.add_parser('exit', help='Exit the CLI')
        cli_commands.add_parser('quit', help='Exit the CLI (alias for exit)')
        cli_commands.add_parser('help', help='Show available commands')
    
    def _setup_readline(self):
        """Setup command history"""
        try:
            import atexit
            import os
            import readline
            
            histfile = os.path.join(os.path.expanduser("~"), ".luna_history")
            try:
                readline.read_history_file(histfile)
                readline.set_history_length(1000)
            except FileNotFoundError:
                pass
            atexit.register(readline.write_history_file, histfile)
            
        except ImportError:
            pass  # No readline available

class CliInputConverter(ApiInputConverter):
    """CLI-specific input converter with integrated input collection"""
    
    def to_api_spec(self, input_obj: Input) -> Dict[str, Any]:
        """Convert to CLI argparse specification"""
        args = []
        
        def process_node(node):
            if isinstance(node, InputField):  # Field-like
                # Skip hidden fields from CLI argument generation
                if getattr(node, 'hidden', False):
                    return []
                
                # Determine argument name format
                param_type = getattr(node, 'param_type', 'named')
                if param_type == "positional":
                    # Only positional arguments don't get -- prefix
                    arg_name = node.name
                else:
                    # All other types (named, flag, variadic) get -- prefix
                    arg_name = f"--{node.name}"
                
                arg_spec = {
                    "name": arg_name,
                    "help": getattr(node, 'description', None)
                }
                
                # Add short name if available
                if hasattr(node, 'short_name') and node.short_name:
                    arg_spec["short"] = f"-{node.short_name}"
                
                # Handle parameter types
                if param_type == "flag":
                    arg_spec["action"] = "store_true"
                elif param_type == "variadic":
                    arg_spec["nargs"] = "+"
                
                # For fields with dict choices, we only expose the display names to argparse
                if hasattr(node, 'choices') and node.choices:
                    display_names = node.get_choice_display_names()
                    if display_names:
                        arg_spec["choices"] = display_names
                
                # Handle default values (but don't make callable defaults visible)
                if hasattr(node, 'default_value') and node.default_value is not None and not callable(node.default_value):
                    arg_spec["default"] = node.default_value
                elif hasattr(node, 'value') and node.value is not None:
                    arg_spec["default"] = node.value
                
                return [arg_spec]
                
            elif isinstance(node, InputGroup):  # Group-like
                # Get all child arguments
                child_args = []
                for child in node.children.values():
                    child_result = process_node(child)
                    if child_result:
                        child_args.extend(child_result)
                
                # Return child arguments directly
                return child_args
            
            return []
        
        # Process the input object
        args = process_node(input_obj)
        
        return {
            "name": input_obj.name,
            "help": getattr(input_obj, 'description', None),
            "args": args
        }

    def display_structure(self, input_obj: Input, context: Dict[str, Any] = None) -> None:
        """Display the CLI input structure"""
        self._display_node_recursive(input_obj, level=0)

    def collect_missing_inputs(self, input_obj: Input, provided_inputs: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Collect missing inputs interactively via CLI"""
        inputs = provided_inputs.copy()                
        success = self._collect_node_inputs_interactive(input_obj, inputs, context)
        
        if success:
            return self._handle_cli_submission(inputs, input_obj.confirm_submit)
        else:
            print("Input collection cancelled")
            return {"success": False, "cancelled": True}
    
    def _collect_node_inputs_interactive(self, node, inputs: Dict[str, Any], context: Dict[str, Any], path: str = "") -> bool:
        """Recursively collect inputs for a node via CLI"""        
        if isinstance(node, InputField):  # Field-like
            # Skip hidden fields - they'll be auto-computed
            if getattr(node, 'hidden', False):
                return True
                
            if node.name not in inputs or inputs[node.name] is None:
                return self._collect_field_input_cli(node, inputs, context)
            else:
                return True
        elif isinstance(node, InputGroup):  # Group-like (including Input)
            if hasattr(node, 'title') and node.title:
                print(f"--- {node.title} ---")
            
            # Collect all children
            for child in node.children.values():
                if not self._collect_node_inputs_interactive(child, inputs, context, f"{path}.{node.name}" if path else node.name):
                    return False
        return True

    def _collect_field_input_cli(self, field: InputField, inputs: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Collect input for a single field via CLI"""
        
        # Handle choice fields with numbered selection
        if hasattr(field, 'choices') and field.choices:
            title = field.title or f"Select {field.name}"
            options = []
            
            # Get display names for choices
            display_names = field.get_choice_display_names()
            for display_name in display_names:
                options.append({
                    'name': display_name,
                    'description': '',
                    'default_value': field.default_value if str(field.default_value) == display_name else None
                })
            
            selected_option, success = self._display_and_select_from_options(title, options)
            if not success:
                return False
            
            # Get the actual value for the selected display name
            selected_value = field.get_choice_value(selected_option['name'])
            inputs[field.name] = selected_value
            return True
        
        # Handle regular fields (existing logic)
        prefill_value = None

        if field.default_value is not None:
            if callable(field.default_value):
                try:
                    current_values = {k: v for k, v in inputs.items()}
                    computed_value = field.compute_dynamic_value(current_values)
                    if computed_value is not None:
                        prefill_value = str(computed_value)
                except:
                    pass
            else:
                prefill_value = str(field.default_value)

        prompt = getattr(field, 'prompt', f"Enter {field.title}: ")

        if field.required:
            prompt = "(required) " + prompt

        while True:
            try:
                if prefill_value:
                    user_input = self._input_with_prefill(prompt, prefill_value)
                else:
                    user_input = input(prompt)
                
                # Handle empty input
                if not user_input:
                    if field.required:
                        print("This field is required")
                        continue
                    else:
                        inputs[field.name] = None
                        return True
                
                # Type conversion
                if field.field_type is bool:
                    user_input = user_input.lower() in ('true', 't', 'yes', 'y', '1')
                elif field.field_type is not str:
                    user_input = field.field_type(user_input)
                
                # Use field's native validation
                validation_result = field.validate(user_input)

                if not validation_result["passed"]:
                    error_msg = validation_result.get('error', {}).get('message', 'Validation failed')
                    print(f"Error: {error_msg}")
                    continue
                
                inputs[field.name] = user_input
                return True
                
            except (ValueError, TypeError) as e:
                print(f"Invalid {field.field_type.__name__}: {e}")
                continue
            except KeyboardInterrupt:
                print("\nInput cancelled")
                return False

    def _display_and_select_from_options(self, title: str, options: list, prompt: str = "Choose option") -> tuple:
        """
        Display numbered options and get user selection.
        
        Args:
            title: Title to display above options
            options: List of dicts with 'name', 'description', and optionally 'default_value'
            prompt: Prompt text for user input
            
        Returns:
            tuple: (selected_option_dict, success_bool)
        """
        print(f"\n{title}:")
        print()
        for i, option in enumerate(options, 1):
            desc = option.get('description', '')
            default_info = f" (current: {option.get('default_value', '')})" if option.get('default_value') else ""
            separator = ' - ' if desc or default_info else ''
            print(f"  {i}. {option['name']}{separator}{desc}{default_info}")
        
        # Get selection
        while True:
            try:
                print()
                choice = input(f"{prompt} (enter number or name): ").strip()
                
                # Try to parse as number first
                try:
                    choice_num = int(choice)
                    if 1 <= choice_num <= len(options):
                        return options[choice_num - 1], True
                    else:
                        print(f"Number must be between 1 and {len(options)}")
                        continue
                except ValueError:
                    # Not a number, try to match by name
                    for option in options:
                        if option['name'].lower() == choice.lower():
                            return option, True
                    
                    # No match found
                    valid_names = [opt['name'] for opt in options]
                    print(f"Invalid choice. Valid options: {', '.join(valid_names)}")
                    continue
                    
            except KeyboardInterrupt:
                print("\nSelection cancelled")
                return None, False

    def _input_with_prefill(self, prompt: str, prefill: str) -> str:
        """Get input with prefilled text that user can edit"""
        try:
            import readline
            
            def startup_hook():
                readline.insert_text(prefill)
                readline.redisplay()
            
            readline.set_startup_hook(startup_hook)
            try:
                result = input(prompt)
            finally:
                readline.set_startup_hook(None)
            
            return result
            
        except ImportError:
            # Fallback if readline not available
            print(f"Prefill: {prefill}")
            return input(prompt)
                
    def _handle_cli_submission(self, inputs: Dict[str, Any], confirm_submit: Optional[bool] = True) -> Dict[str, Any]:
        """Handle CLI input submission"""
        if confirm_submit is False:
            return {"success": True, "inputs": inputs}

        print("\n=== Summary ===")
        for name, value in inputs.items():
            print(f"{name}: {value}")
        
        # Confirm submission
        response = input("\nSubmit? [Y/n]: ").strip().lower()
        if response and response not in ['y', 'yes']:
            return {"success": False, "cancelled": True}
        
        return {"success": True, "inputs": inputs}
    
    def _display_node_recursive(self, node, level: int = 0):
        """Recursively display node structure for CLI"""
        indent = "  " * level
        
        if isinstance(node, InputField):  # Field-like
            # Show hidden fields in display but mark them
            hidden_marker = " (auto)" if getattr(node, 'hidden', False) else ""
            value_display = getattr(node, 'value', "(empty)")
            print(f"{indent}{node.title}{hidden_marker}: {value_display}")
        elif isinstance(node, InputGroup):  # Group-like (including Input)
            if hasattr(node, 'title'):
                print(f"{indent}[{node.title}]")
            for child in node.children.values():
                self._display_node_recursive(child, level + 1)