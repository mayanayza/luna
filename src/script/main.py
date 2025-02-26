import argparse
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.script.channels._registry import ChannelRegistry
from src.script.channels.github import GithubHandler
from src.script.channels.instagram import InstagramHandler
from src.script.channels.pdf import PDFHandler
from src.script.channels.project import ProjectHandler
from src.script.channels.raw import RawHandler
from src.script.channels.website import WebsiteHandler
from src.script.config import Config

load_dotenv()

def setup_channel_registry(config):
    """Set up the channel registry with all available handlers"""
    registry = ChannelRegistry(config)
    
    # Initialize all handlers
    github_handler = GithubHandler(config)
    website_handler = WebsiteHandler(config)
    pdf_handler = PDFHandler(config)
    raw_handler = RawHandler(config)
    instagram_handler = InstagramHandler(config)
    
    # Create project handler with dependencies
    project_handler = ProjectHandler(
        config=config,
        github_handler=github_handler,
        website_handler=website_handler,
        raw_handler=raw_handler
    )
    
    # Register handlers' commands
    github_handler.register_commands(registry)
    project_handler.register_commands(registry)
    website_handler.register_commands(registry)
    pdf_handler.register_commands(registry)
    raw_handler.register_commands(registry)
    instagram_handler.register_commands(registry)
    
    return registry

def parse_arguments():
    parser = argparse.ArgumentParser(description='Project Management and Publication Tool')
    
    # Main command argument
    parser.add_argument('command', help='Command to execute: create, list, rename, delete, init, stage, publish')
    
    # Channel to operate on
    parser.add_argument('--channel', '-ch', help='Channel to use (github, web, pdf, instagram, raw, project)')
    
    # Project selection arguments
    parser.add_argument('--all-projects', default=False, action='store_true', help='Apply command to all projects')
    parser.add_argument('--projects', '-p', nargs='+', help='One or more projects to operate on')
    
    # Channel selection arguments (for compatibility with old interface)
    parser.add_argument('--all-channels', default=False, action='store_true', help='Apply command across all channels')
    parser.add_argument('--channels', nargs='+', help='One more channels to publish to (web, pdf, github)')
    
    # PDF-specific arguments
    parser.add_argument('--collate-images', '-ci', action='store_true', help='Collate images for PDF publication')
    parser.add_argument('--submission-name', '-sn', help='Name of what pdf is being submitted to')
    parser.add_argument('--max-width', '-mw', help='Max width for images when generating separate image files for PDF publication')
    parser.add_argument('--max-height', '-mh', help='Max height for images when generating separate image files for PDF publication')
    parser.add_argument('--filename-prepend', '-fp', default='', help='Prepend string for PDF filename')

    # GitHub-specific arguments
    parser.add_argument('--commit-message','-cm', default='', help='Commit message for publishing to github')

    # Instagram-specific arguments
    parser.add_argument('--caption','-ca', default='', help='Caption for Instagram post. Defaults to project tagline.')
    
    # List projects sorting/filtering
    parser.add_argument('--sort-by', choices=['name', 'date', 'priority', 'status'], default='name', 
                         help='Sort projects by this field when listing')
    parser.add_argument('--status', choices=['backlog', 'in_progress', 'complete', 'archive'], 
                         help='Filter projects by status when listing')
    
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
        instagram_username=(os.environ.get('INSTAGRAM_USERNAME')),
        instagram_password=(os.environ.get('INSTAGRAM_PASSWORD')),
        enable_things3=os.environ.get('ENABLE_THINGS3', 'false').lower() == 'true',
        things3_area=os.environ.get('THINGS3_AREA', '')
    )
    
    channels = setup_channel_registry(config)

    try:
        # Handle command execution through channel registry
        if args.command in ['create', 'list', 'rename', 'delete']:
            # Project management commands always use the project channel
            channels.command(
                command=args.command, 
                channels=['project'],
                sort_by=args.sort_by, 
                status=args.status,
                projects=args.projects,
                all_projects=args.all_projects
            )
        elif args.command == 'init':
            # GitHub initialization if not done in project creation
            if not args.projects and not args.all_projects:
                print("Error: You must specify a project with --projects or use --all-projects")
                sys.exit(1)
            channels.command(
                command=args.command, 
                channels=['github'], 
                projects=args.projects,
                all_projects=args.all_projects
            )
        elif args.command in ['publish', 'stage']:
            # Publishing commands
            target_channels = args.channels if args.channels else [args.channel] if args.channel else None
            
            try:
                channels.command(
                    command=args.command,
                    channels=target_channels,
                    all_channels=args.all_channels,
                    projects=args.projects,
                    all_projects=args.all_projects,
                    **{k: v for k, v in vars(args).items() if k not in ['command', 'channels', 'all_channels', 'projects', 'all_projects', 'channel']}
                )
            except ValueError as e:
                print(f"Command error: {e}")
                sys.exit(1)
        else:
            print(f"Unknown command: {args.command}")
            sys.exit(1)
            
    except Exception as e:
        logging.error(f"Operation failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()