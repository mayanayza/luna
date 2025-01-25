import argparse
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from script.src.automation import Automation
from script.src.channels._registry import ChannelRegistry
from script.src.config import Config

load_dotenv()

def setup_channel_registry(automation, config):

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
            commit_message=kwargs.get('commit_message', ''), 
        )
    )
    
    return registry

def parse_arguments():
    parser = argparse.ArgumentParser(description='Project Publication Tool')
    parser.add_argument('--command', '-c', help='Command to execute. Create, list, rename, or publish.')
    
    parser.add_argument('--all-projects', default=False, action='store_true', help='Publish for all projects')
    parser.add_argument('--projects', '-p', nargs='+', help='Specific projects to publish.')
    
    parser.add_argument('--all-channels', default=False, action='store_true', help='Publish across all channels')
    parser.add_argument('--channels', '-ch', nargs='+', help='Channels to publish to (web, pdf, github). Use "all" to publish to all channels.')
    
    parser.add_argument('--collate-images', action='store_true', help='Collate images for PDF publication')
    parser.add_argument('--filename-prepend', default='', help='Prepend string for PDF filename')

    parser.add_argument('--commit-message', default='', help='Commit message for publishing to github')
    
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
    channels = setup_channel_registry(automation, config)

    try:
        
        if args.command == 'create':
            automation.create_project()
        elif args.command == 'list':
            automation.list_projects()
        elif args.command == 'rename':
            automation.rename_project()
        elif args.command == 'publish':

            try:
                # Publish based on command-line arguments
                channels.publish(**vars(args))
            except ValueError as e:
                print(f"Publication error: {e}")
                sys.exit(1)
            
    except Exception as e:
        logging.error(f"Operation failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()