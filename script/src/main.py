import argparse
import logging
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

from script.src.automation import Automation
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

def main():
    parser = argparse.ArgumentParser(description='Project Automation Tool')
    parser.add_argument('--command', choices=['create', 'publish', 'rename', 'list'], default='create', 
                       help='Command to execute')
    parser.add_argument('--all', action='store_true', help='Flag to publish all projects, roadmap, and website')
    parser.add_argument('--project', help='Flag to publish a specific project')
    parser.add_argument('--allprojects', action='store_true', help='Flag to publish all projects')
    parser.add_argument('--website', action='store_true', help='Flag to publish website')
    parser.add_argument('--roadmap', action='store_true', help='Flag to publish roadmap')
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
            
        elif args.command == 'list':
            automation.list_projects()

        elif args.command == 'publish':
            if args.all:
                automation.publish_all()
            elif args.project:
                automation.publish_project(args.project)
            elif args.allprojects:
                automation.publish_all_projects()
            elif args.website:
                automation.publish_website()
            elif args.roadmap:
                automation.publish_roadmap()
            else:
                parser.error("Either --name or --all must be specified for publish command")
                
        elif args.command == 'rename':
            if not args.project:
                parser.error("--project is required for rename command")
            new_name, new_display_name = prompt_for_new_name(args.project)
            automation.rename_project(args.project, new_name, new_display_name)
            
    except Exception as e:
        logging.error(f"Operation failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()