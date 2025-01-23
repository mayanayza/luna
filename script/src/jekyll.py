import os
import shutil
import subprocess
from pathlib import Path

import yaml

from script.src.config import Config
from script.src.constants import MEDIA_TYPES, Files, Status
from script.src.github import GithubHandler
from script.src.utils import (
    get_media_path,
    get_project_directories,
    get_project_metadata,
    get_project_path,
    setup_logging,
    strip_emoji,
)


class JekyllHandler:

    def __init__(self, config: Config):
        self.config = config
        self.github = GithubHandler(config)
        print(self.github)
        self.logger = setup_logging(__name__)

    @property
    def posts_dir(self) -> Path:
        return self.config.jekyll_dir / '_posts'

    @property
    def media_dir(self) -> Path:
        return self.config.jekyll_dir / 'media'

    @property
    def pages_dir(self) -> Path:
        return self.config.jekyll_dir / '_pages'

    def publish_post(self, name: str) -> None:
            """Generate Jekyll post content from project metadata"""
            project_dir = get_project_path(self, name)

            metadata = get_project_metadata(self, name)
            project = metadata['project']
            
            # Build front matter
            front_matter = {
                'layout': 'post',
                'title': strip_emoji(project['display_name']).strip(),
                'description': project.get('description', ''),
                'date': f"{project['date_created']} 15:01:35 +0300",
                'tags': project.get('tags', []),
                'github': f"{self.github.url_path}/{name}"
            }

            featured_image = project.get('featured_image')
            if featured_image:
                featured_image_path = f"/media/{project['name']}/images/{featured_image}"
                front_matter['image'] = featured_image_path
            
            with open(project_dir / Files.CONTENT, 'r') as f:
                content = f.read()
                    
            # Add image gallery if images exist
            extensions = ("*.png","*.jpg","*.jpeg", "*.JPG", "*.JPEG")
            images = []
            for extension in extensions:
                images.extend( get_media_path(self, project_dir, 'images').glob(extension) )
            if images:
                content += '\n\n<div class="gallery-box">\n  <div class="gallery">\n'
                for img in images:
                    if img.name != project.get(self, 'featured_image', ''):  # Skip featured image
                        content += f'    <img src="/media/{project["name"]}/images/{img.name}">\n'
                content += '  </div>\n</div>\n'
            
            # Add videos if they exist
            videos = list( get_media_path(self, project_dir, 'videos').glob('*.webm') )
            if videos:
                for video in videos:
                    content += f'\n\n<video controls>\n  <source src="/media/{project["name"]}/videos/{video.name}" type="video/webm">\n</video>\n'
            
            # Add models if they exist
            models = list( get_media_path(self, project_dir, 'models').glob('*.glb'))
            if models:
                for model in models:
                    content += f'\n\n<model-viewer src="/media/{project["name"]}/models/{model.name}" auto-rotate camera-controls></model-viewer>\n'
            
            self.logger.info(f"Successfully generated Jekyll post for {name}")

            # Combine front matter and content

            post = "---\n"
            post += f"{yaml.dump(front_matter, default_flow_style=False, sort_keys=False, allow_unicode=True)}\n"
            post += "---\n"

            os.chdir(project_dir)
            visibility = subprocess.run(['gh', 'repo', 'view', '--json', 'visibility', '-q', '.visibility'], capture_output=True, text=True)
            visibility = visibility.stdout.strip().upper()
            if visibility == 'PUBLIC':
                post += f"[View on GitHub]({self.github.url_path}/{name})\n\n"
            post += f"{content}\n"

            post_date = metadata['project']['date_created']
            post_file = self.jekyll.posts_dir / f"{post_date}-{name}.md"
            with open(post_file, 'w') as f:
                f.write(post)

    def publish_roadmap(self) -> None:
        """Generate roadmap page from projects metadata"""
        projects = get_project_directories(self)
        in_progress = []
        backlog = []
        public_repos = []
        
        for project_dir, name in projects:

            with open(project_dir / Files.METADATA, 'r') as f:
                metadata = yaml.safe_load(f)
                project = metadata['project']
                name = metadata['project']['name']

                os.chdir(project_dir)
                visibility = subprocess.run(['gh', 'repo', 'view', '--json', 'visibility', '-q', '.visibility'], capture_output=True, text=True)
                visibility = visibility.stdout.strip().upper()
                if visibility == 'PUBLIC':
                    public_repos.append(name)

                if project['status'] == Status.IN_PROGRESS:
                    in_progress.append(project)
                elif project['status'] == Status.BACKLOG:
                    backlog.append(project)
        
        # Sort by priority
        #in_progress.sort(key=lambda x: x.get('priority', 0), reverse=True)
        backlog.sort(key=lambda x: x.get('priority', 0), reverse=True)

        content = "---\n"
        content += "layout: page\n"
        content += "title: Roadmap\n"
        content += "permalink: /roadmap/\n"
        content += "---\n"

        content += "\n## In Progress\n"
        if in_progress:
            content += "\n| Project | Description |\n|---------|-------------|\n"
            for project in in_progress:
                if project['name'] in public_repos:
                    content += f"| <a href='{self.github.url_path}/{project['name']}' target='_blank'>{project['display_name']}</a> | {project.get('description', '')} | \n"
                else:
                    content += f"| {project['display_name']} | {project.get('description', '')} | \n"
        else:
            content += "Nothing currently in progress"
        
        content += "\n## Backlog\n"
        if backlog:
            content += "\n| Project | Description | Priority |\n|---------|-------------|----------|\n"
            for project in backlog:
                content += f"| {project['display_name']} | {project.get('description', '')} | {project.get('priority', 0)} |\n"
        else:
            content += "Nothing currently in backlog"

        # Publish roadmap
        self.jekyll_pages_dir.mkdir(exist_ok=True)
        with open(self.jekyll_pages_dir / 'roadmap.md', 'w') as f:
            f.write(content)

        self.logger.info("Successfully generated and synced roadmap")

    def publish_media(self, source_dir: Path, dest_dir: Path) -> None:
        """Sync media files from project to Jekyll site"""
        if not source_dir.exists():
            return
            
        # Create destination directories
        for media_type in MEDIA_TYPES:
            (dest_dir / media_type).mkdir(parents=True, exist_ok=True)
            
            # Copy files
            source_type_dir = source_dir / media_type
            if source_type_dir.exists():
                for file in source_type_dir.iterdir():
                    if file.is_file():
                        shutil.copy2(file, dest_dir / media_type / file.name)

        self.logger.info("Successfully synced Jekyll media files")

    def rename(self, old_name: str, new_name: str, display_name: str) -> None:
        """Update all Jekyll-related files when renaming a project"""
        try:
            # Remove post file in _posts directory (will be recreated)
            jekyll_posts_dir = self.jekyll_posts_dir
            for post_file in jekyll_posts_dir.glob(f'*-{old_name}.md'):
                post_file.unlink()

            # Rename media directory
            old_media_dir = self.jekyll_media_dir / old_name
            if old_media_dir.exists():
                new_media_dir = self.jekyll_media_dir / new_name
                # Create parent directories if they don't exist
                new_media_dir.parent.mkdir(parents=True, exist_ok=True)
                old_media_dir.rename(new_media_dir)
                self.logger.info(f"Renamed media directory from {old_name} to {new_name}")

        except Exception as e:
            self.logger.error(f"Failed to rename Jekyll files: {e}")
            raise
