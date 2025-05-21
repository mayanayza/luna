import argparse

from src.script.constants import EntityType
from src.script.entity._api import Api


class Cli(Api):

    def __init__(self, registry):

        # Set name before parent init for proper registration
        self.name = 'cli'

        # Initialize base class
        super().__init__(registry)
        
        # Create parser and register arguments
        self.parser = argparse.ArgumentParser(description='Luna CLI')
        self._registered_args = set()
        
        # Add core arguments
        self._setup_core_arguments()
        
        


    def _setup_core_arguments(self):
        # Command argument
        self.parser.add_argument('command', help='Command to execute: create, list, rename, delete, etc.')
        
        # Project-related arguments
        self.parser.add_argument('--project', '-p', help='Project to operate on')
        self.parser.add_argument('--projects', nargs='+', help='One or more projects to operate on')
        self.parser.add_argument('--all-projects', default=False, action='store_true', help='Apply command to all projects')
        
        # Integration-related arguments
        self.parser.add_argument('--integration', '-i', help='Integration to use')
        self.parser.add_argument('--integrations', nargs='+', help='One or more integrations to use')
        self.parser.add_argument('--all-integrations', default=False, action='store_true', help='Apply command across all integrations')
        
        # Other common arguments
        self.parser.add_argument('--sort-by', choices=['name', 'date', 'priority', 'status'], default='name', help='Sort by field when listing')
        
        # Register common arguments that multiple integrations might use
        self._add_argument('--commit-message', '-cm', default='', help='Commit message for publishing content')

    def _add_argument(self, *args, **kwargs):
        """
        Add an argument to the parser, but only if it hasn't been added already.
        Returns True if the argument was added, False if it was already registered.
        """
        # Extract argument names from args (they start with -)
        arg_names = {arg for arg in args if arg.startswith('-')}
        
        # Check if any of these argument names are already registered
        if arg_names.intersection(self._registered_args):
            # At least one of the argument names is already registered, so skip it
            return False
        
        # None of the argument names are registered yet, so add them all
        self._registered_args.update(arg_names)
        
        try:
            self.parser.add_argument(*args, **kwargs)
            return True
        except Exception as e:
            self.logger.warning(f"Error adding argument {args}: {e}")
            return False

    def start(self, app_context):
        """Process command line arguments and dispatch commands."""
        try:
            args = self.parser.parse_args()
            self._process_command(args, app_context)
        except Exception as e:
            self.logger.error(f"Error processing command: {e}")
            import traceback
            traceback.print_exc()

    def _process_command(self, args, app_context):
        """
        Process a command based on parsed arguments.
        
        Args:
            args: The parsed command line arguments
            app_context: The application context
        """
        command = args.command
        
        # Get required registries
        project_registry = app_context.registry_manager.get_registry(EntityType.PROJECT)
        integration_registry = app_context.registry_manager.get_registry(EntityType.INTEGRATION)
        
        if not project_registry or not integration_registry:
            self.logger.error("Required registries not found")
            return
        
        # Handle registry-level commands first
        if command in ['list', 'create']:
            self._handle_registry_command(args, project_registry, integration_registry)
            return
            
        # Handle integration-specific commands  
        elif args.integration or args.integrations or args.all_integrations:
            self._handle_integration_command(args, integration_registry)
            return
        
        # Handle project-specific commands
        elif args.project or args.projects or args.all_projects:
            self._handle_project_command(args, project_registry)
            return
        
        # Handle unknown commands
        else:
            self.logger.warning(f"Unknown command: {command}")
            self.parser.print_help()

    def _handle_integration_command(self, args, integration_registry):
        """Handle commands that target integrations."""
        command = args.command
        
        # Prepare targets
        targets = {}
        
        # Add integration targets
        if args.all_integrations:
            targets['integrations'] = True
        elif args.integrations:
            targets['integrations'] = args.integrations
        elif args.integration:
            targets['integrations'] = [args.integration]
        
        # Add project targets if specified
        if args.all_projects:
            targets['projects'] = True
        elif args.projects:
            targets['projects'] = args.projects
        elif args.project:
            targets['projects'] = [args.project]
        
        # Extract additional parameters
        params = {k: v for k, v in vars(args).items() if k not in [
            'command', 'integration', 'integrations', 'all_integrations',
            'project', 'projects', 'all_projects'
        ]}
        
        # Dispatch command
        result = integration_registry.dispatch_entity_command(command, targets, **params)
        
        # Display results
        self._display_results(result)
    
    def _handle_project_command(self, args, project_registry):
        """Handle commands that target projects."""
        command = args.command
        
        # Handle special commands that need interactive prompting
        if command == "rename":
            return self._handle_project_rename(args, project_registry)
            
        # Prepare targets for standard commands
        targets = {}
        
        # Add project targets
        if args.all_projects:
            targets['projects'] = True
        elif args.projects:
            targets['projects'] = args.projects
        elif args.project:
            targets['projects'] = [args.project]
        
        # Extract additional parameters
        params = {k: v for k, v in vars(args).items() if k not in [
            'command', 'project', 'projects', 'all_projects'
        ]}
        
        # Dispatch command
        result = project_registry.dispatch_entity_command(command, targets, **params)
        
        # Display results
        self._display_results(result)
        
    def _handle_registry_command(self, args, project_registry, integration_registry):
        """Handle commands that operate at the registry level."""
        command = args.command
        
        # Extract parameters
        params = {k: v for k, v in vars(args).items() if k != 'command'}
        
        if command == 'list':
            # Determine which registry to list
            if args.integration or args.integrations or args.all_integrations:
                result = integration_registry.dispatch_registry_command('list', **params)
                self._display_list_results(result, 'integrations')
            else:
                result = project_registry.dispatch_registry_command('list', **params)
                self._display_list_results(result, 'projects')
        
        elif command == 'create':
            # Handle project creation
            if not args.integration and not args.integrations:
                # Get project details through interactive prompt
                project_name, project_title, project_emoji = self._prompt_for_project_details()
                
                # Validate project name uniqueness
                while project_registry.get_by_name(project_name):
                    print(f"Project with name '{project_name}' already exists.")
                    project_name, project_title, project_emoji = self._prompt_for_project_details()
                
                # Dispatch create command to project registry
                result = project_registry.dispatch_registry_command('create', 
                                                                   name=project_name, 
                                                                   title=project_title, 
                                                                   emoji=project_emoji)
                
                if result:
                    self.logger.info(f"Created project: {result.get('name')}")
            else:
                # No support for integration creation at this time
                self.logger.warning("Creation of integrations is not supported via CLI")

    def _handle_project_rename(self, args, project_registry):
        """Handle project rename operation."""
        # Get project
        project_name = args.project
        if not project_name:
            project_name = input("Enter name of project to rename: ").strip()
            
        project = project_registry.get_by_name(project_name)
        if not project:
            self.logger.error(f"Project '{project_name}' not found")
            return
            
        # Get new title
        new_title = input(f"Enter new title (or press Enter to keep current '{project.title}'): ").strip() or None
        
        # Get new emoji
        new_emoji = input(f"Enter new emoji prefix (or press Enter to keep current '{project.emoji}'): ").strip() or None
        
        # Validate emoji if provided
        if new_emoji and not self._is_valid_emoji(new_emoji):
            self.logger.error("Invalid emoji provided.")
            return
        
        # Generate new name from title if title changed
        if new_title:
            from src.script.utils import format_name
            new_name = format_name(new_title)
        else:
            new_name = project.name
        
        # Confirm uniqueness
        if new_name != project_name and project_registry.get_by_name(new_name):
            self.logger.error(f"Project with name '{new_name}' already exists")
            return
            
        # Confirm changes
        print("\nProject will be updated with these details:")
        print(f"Name: {new_name}")
        print(f"Title: {new_title if new_title else project.title}")
        if new_emoji or project.emoji:
            print(f"Emoji: {new_emoji if new_emoji is not None else project.emoji}")
        
        # Show display title
        display_emoji = new_emoji if new_emoji is not None else project.emoji
        display_title = new_title if new_title is not None else project.title
        if display_emoji:
            print(f"Display title: {display_emoji} {display_title}")
        else:
            print(f"Display title: {display_title}")
        
        confirm = input("\nConfirm these changes? (y/n): ").strip().lower()
        if confirm != 'y':
            self.logger.info("Operation cancelled")
            return
            
        # Execute rename
        result = project_registry.dispatch_entity_command(
            'rename', 
            targets={'projects': [project_name]},
            new_name=new_name,
            new_title=new_title,
            new_emoji=new_emoji
        )
        
        if result:
            self.logger.info(f"Renamed project from '{project_name}' to '{new_name}'")
        else:
            self.logger.error("Failed to rename project")
    
    def _prompt_for_project_details(self):
        """
        Prompt user for project title and optional emoji.
        
        Returns:
            tuple: (name, title, emoji)
        """
        while True:
            # Get project title
            title = input("Enter project title: ").strip()
            if not title:
                print("Project title cannot be empty. Please try again.")
                continue
                
            # Get optional emoji
            emoji = input("Enter an emoji prefix (optional): ").strip()
            
            # Validate emoji if provided
            if emoji and not self._is_valid_emoji(emoji):
                print("Invalid emoji. Please enter a valid emoji or leave blank.")
                continue
                
            # Generate name from title
            from src.script.utils import format_name
            name = format_name(title)
            
            # Display details for confirmation
            print("\nProject details:")
            print(f"Name: {name}")
            print(f"Title: {title}")
            if emoji:
                print(f"Emoji: {emoji}")
                print(f"Display title: {emoji} {title}")
            else:
                print("Emoji: None")
                print(f"Display title: {title}")
            
            confirm = input("\nConfirm these details? (y/n): ").strip().lower()
            if confirm == 'y':
                return name, title, emoji
                
            print("Let's try again.")


    def _display_results(self, results):
        """Display command execution results."""
        if not results:
            self.logger.info("No results returned")
            return
        
        # For now, just log the results
        for registry_id, registry_results in results.items():
            self.logger.info(f"Results from {registry_id}:")
            for result in registry_results:
                if isinstance(result, dict):
                    for key, value in result.items():
                        self.logger.info(f"  {key}: {value}")
                else:
                    self.logger.info(f"  {result}")
    
    def _display_list_results(self, items, item_type):
        """Display list results in a formatted table."""
        if not items:
            self.logger.info(f"No {item_type} found")
            return
        
        # Format items as a table (simple implementation)
        self.logger.info(f"\n--- {item_type.upper()} ---")
        for item in items:
            self.logger.info(f"{item.get('name', 'Unknown')}: {item}")