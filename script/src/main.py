import argparse
import logging
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

from script.src.automation import Automation
from script.src.config import Config
from script.src.constants import Files
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

def main():
    parser = argparse.ArgumentParser(description='Project Automation Tool')
    parser.add_argument('--command', choices=['create', 'publish', 'rename', 'list'], default='create', help='Command to execute')
    
    parser.add_argument('--channel', nargs='+', help='Publish to specific channels: web, pdf, github. Will publish to all if not provided.')
    parser.add_argument('--projects', nargs='+', help='Input to specify one or more specific project name for publish and rename automation')
    parser.add_argument('--all', default=False, action='store_true', help='Flag to run publication workflows for all projects')

    parser.add_argument('--collate_images', default=False, action='store_true', help='Add images to PDF for PDF publish')
    parser.add_argument('--filename_prepend', default='', help='Prepend text to image filenames for PDF publish')

    args = parser.parse_args()

    # Calculate templates directory relative to script location

    config = Config(
        base_dir=Path(os.environ.get('PROJECT_BASE_DIR')),
        website_domain=os.environ.get('WEBSITE_DOMAIN'),
        github_username=os.environ.get('GITHUB_USERNAME'),
        github_token=os.environ.get('GITHUB_TOKEN'),
        jekyll_dir=Path(os.environ.get('JEKYLL_DIR')),
        enable_things3=os.environ.get('ENABLE_THINGS3', 'true').lower() == 'true'
    )

    try:
        automation = Automation(config)
        
        if args.command == 'create':
            name, display_name = prompt_for_name()
            automation.create_project(name, display_name)
        elif args.command == 'rename':
                new_name, new_display_name = prompt_for_new_name(args.project)
                automation.rename_project(args.project, new_name, new_display_name)
        else:

            projects = []

            if args.all:
                for item in config.base_dir.iterdir():
                    if item.is_dir() and (item / Files.METADATA).exists():
                        projects.append(item.name)
            elif args.projects:
                projects = args.projects
            else:
                raise ValueError('Must include at least one project using --project arg or specify --all')

            if args.command == 'list':
                automation.list_projects(projects)

            elif args.command == 'publish':

                if not args.channel:
                    automation.publish_website(projects)
                    automation.publish_pdf(projects)
                    automation.publish_github(projects)
                else:
                    if 'web' in args.channel:
                        automation.publish_website(projects)
                    if 'pdf' in args.channel:
                        automation.publish_pdf(projects, args.collate_images, args.filename_prepend)
                    if 'github' in args.channel:
                        automation.publish_github(projects)
                
            
            
    except Exception as e:
        logging.error(f"Operation failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()