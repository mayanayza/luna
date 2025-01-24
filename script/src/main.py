import argparse
import logging
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

from script.src.automation import Automation
from script.src.channels._registry import ChannelRegistry
from script.src.config import Config
from script.src.utils import strip_emoji

load_dotenv()

def get_formatted_name(name: str) -> str:
    # Remove emoji and other special characters, convert to lowercase
    cleaned = strip_emoji(name)
    cleaned = re.sub(r'[^a-zA-Z0-9\s-]', '', cleaned)
    
    # Convert to kebab-case
    formatted = cleaned.strip().lower().replace(' ', '-')
    formatted = re.sub(r'-+', '-', formatted)
    
    return formatted

def prompt_for_name() -> tuple[str, str]:
    """Prompt user for project name and return (name, formatted_name)"""
    display_name = input("Enter project display name (e.g. '🌱 Project Name; a canonical name will be generated like project-name.'): ").strip()
    if not display_name:
        raise ValueError("Project name cannot be empty")
    
    name = get_formatted_name(display_name)
    
    print("\nProject details:")
    print(f"Name: {name}")
    print(f"Formatted name: {display_name}")
    
    confirm = input("\nConfirm these details? (y/n): ").strip().lower()
    if confirm != 'y':
        raise ValueError("Project creation cancelled by user")
    
    return name, display_name

def prompt_for_new_name(old_name: str) -> tuple[str, str]:
    """Prompt user for new project name and return (name, formatted_name)"""
    new_display_name = input("Enter project display name (e.g. '🌱 Project Name; a canonical name will be generated like project-name.'): ").strip()
    if not new_display_name:
        raise ValueError("New project name cannot be empty")
    
    new_name = get_formatted_name(new_display_name)
    
    print("\nRename details:")
    print(f"Old name: {old_name}")
    print(f"New name: {new_name}")
    print(f"New display name: {new_display_name}")
    
    confirm = input("\nConfirm these details? (y/n): ").strip().lower()
    if confirm != 'y':
        raise ValueError("Project rename cancelled by user")
    
    return new_name, new_display_name

def setup_publication_registry(automation, config):

    registry = ChannelRegistry(config)
    
    # Register publication channels
    registry.register('web', lambda **kwargs: 
        automation.publish_web(
            kwargs.get('projects', []), 
        )
    )
    
    registry.register('pdf', lambda **kwargs: 
        automation.publish_pdf(
            kwargs.get('projects', []),
            collate_images=kwargs.get('collate_images', False), 
            filename_prepend=kwargs.get('filename_prepend', '')
        )
    )
    
    registry.register('github', lambda **kwargs: 
        automation.publish_github(
            kwargs.get('projects', []),
        )
    )
    
    return registry

def parse_arguments():
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments object
    """    
    parser = argparse.ArgumentParser(description='Project Publication Tool')
    
    parser.add_argument('--command', '-c', 
                        help='Command to execute. Create, list, rename, or publish.')

    parser.add_argument('--projects', '-p', 
                        nargs='+', 
                        help='Specific projects to publish. Use "all" to publish all projects.')
        
    parser.add_argument('--channel', '-ch', 
                        nargs='+', 
                        help='Channels to publish to (web, pdf, github). Use "all" to publish to all channels.')
    
    parser.add_argument('--collate-images', 
                        action='store_true', 
                        help='Collate images for PDF publication')
    
    parser.add_argument('--filename-prepend', 
                        default='', 
                        help='Prepend string for PDF filename')
    
    return parser.parse_args()


def main():

    args = parse_arguments()
    config = Config(
        base_dir=Path(os.environ.get('PROJECT_BASE_DIR')),
        website_domain=os.environ.get('WEBSITE_DOMAIN'),
        github_username=os.environ.get('GITHUB_USERNAME'),
        github_token=os.environ.get('GITHUB_TOKEN'),
        jekyll_dir=Path(os.environ.get('JEKYLL_DIR')),
        enable_things3=os.environ.get('ENABLE_THINGS3', 'true').lower() == 'true'
    )
    automation = Automation(config)
    publication_registry = setup_publication_registry(automation, config)

    print(args.command)

    try:
        
        if args.command == 'create':
            name, display_name = prompt_for_name()
            automation.create_project(name, display_name)
        elif args.command == 'list':
            automation.list_projects()
        elif args.command == 'rename':
            new_name, new_display_name = prompt_for_new_name(args.project)
            automation.rename_project(args.project, new_name, new_display_name)
        elif args.command == 'publish':

            try:
                # Publish based on command-line arguments
                publication_registry.publish(
                    channels=args.channel, 
                    projects=args.projects,
                    collate_images=args.collate_images, 
                    filename_prepend=args.filename_prepend
                )
            except ValueError as e:
                print(f"Publication error: {e}")
                sys.exit(1)
            
    except Exception as e:
        logging.error(f"Operation failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()