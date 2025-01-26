import argparse
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.script.automation import Automation
from src.script.channels._registry import ChannelRegistry
from src.script.config import Config

load_dotenv()

def setup_channel_registry(automation, config):

    registry = ChannelRegistry(config)
    
    # Register publication channels
    registry.register('web', {
        'stage': lambda **kwargs: automation.stage_web(
            kwargs.get('projects', [])
        ),
        'publish': lambda **kwargs: automation.publish_web(
            kwargs.get('projects', [])
        )
    })
    
    registry.register('pdf', {
        'publish': lambda **kwargs: automation.publish_pdf(
            kwargs.get('projects', []),
            collate_images=kwargs.get('collate_images', False), 
            filename_prepend=kwargs.get('filename_prepend', ''),
            max_width=kwargs.get('max_width', ''),
            max_height=kwargs.get('max_height', '')
        )
    })

    registry.register('github', {
        'stage': lambda **kwargs: automation.stage_github(
            kwargs.get('projects', []),
            commit_message=kwargs.get('commit_message', '')
        ),
        'publish': lambda **kwargs: automation.publish_github(
            kwargs.get('projects', []),
            commit_message=kwargs.get('commit_message', '')
        ),
    })
    

    registry.register('raw', {
        'publish': lambda **kwargs: automation.publish_raw(
            kwargs.get('projects', []),
        )
    })

    
    
    return registry

def parse_arguments():
    parser = argparse.ArgumentParser(description='Project Publication Tool')
    parser.add_argument('--command', '-c', help='Command to execute. Create, list, rename, publish, stage, delete.')
    
    parser.add_argument('--all-projects', default=False, action='store_true', help='Stage or publish for all projects')
    parser.add_argument('--projects', '-p', nargs='+', help='One or more projects to stage or publish.')
    
    parser.add_argument('--all-channels', default=False, action='store_true', help='Stage or publish across all channels')
    parser.add_argument('--channels', '-ch', nargs='+', help='One more channels to publish to (web, pdf, github).')
    
    parser.add_argument('--collate-images', '-ci', action='store_true', help='Collate images for PDF publication')
    parser.add_argument('--max-width', '-mw', help='Max width for images when generating separate image files for PDF publication')
    parser.add_argument('--max-height', '-mh', help='Max height for images when generating separate image files for PDF publication')
    parser.add_argument('--filename-prepend', '-fp', default='', help='Prepend string for PDF filename')

    parser.add_argument('--commit-message','-cm', default='', help='Commit message for publishing to github')
    
    return parser.parse_args()


def main():

    args = parse_arguments()
    config = Config(
        base_dir=Path(os.environ.get('PROJECT_BASE_DIR')),
        website_domain=os.environ.get('WEBSITE_DOMAIN'),
        github_username=os.environ.get('GITHUB_USERNAME'),
        github_token=os.environ.get('GITHUB_TOKEN'),
        website_dir=Path(os.environ.get('WEBSITE_DIR')),
        website_posts=(os.environ.get('WEBSITE_POSTS')),
        website_media=(os.environ.get('WEBSITE_MEDIA')),
        website_pages=(os.environ.get('WEBSITE_PAGES')),
        enable_roadmap=os.environ.get('ENABLE_ROADMAP').lower() == 'true',
        enable_things3=os.environ.get('ENABLE_THINGS3').lower() == 'true',
        things3_area=os.environ.get('THINGS3_AREA')
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
        elif args.command == 'delete':
            automation.delete_project()
        elif args.command == 'publish' or args.command == 'stage':

            try:
                # Publish based on command-line arguments
                channels.command(**vars(args))
            except ValueError as e:
                print(f"Publication error: {e}")
                sys.exit(1)
            
    except Exception as e:
        logging.error(f"Operation failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()