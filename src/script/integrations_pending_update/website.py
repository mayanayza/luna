import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict

import yaml

from src.script.constants import Media
from src.script.integration._integration import Integration
from src.script.integration._registry import IntegrationRegistry
from src.script.project._project import Project
from src.script.utils import (
    convert_model_file,
    convert_video_file,
    load_personal_info,
    resize_image_file,
)


class WebsiteIntegration(Integration):

    def __init__(self, registry: IntegrationRegistry):
        config = {
            'name': 'website',
            'env': {
                'dir':'WEBSITE_DIR',
                'base_url':'WEBSITE_DOMAIN',
                'posts_folder_name':'WEBSITE_POSTS',
                'media_folder_name':'WEBSITE_MEDIA',
                'pages_folder_name':'WEBSITE_PAGES',
                'data_folder_name':'WEBSITE_DATA'
            },
            'project_fields':{
                'feature_post': False,
                'show_written_content': False,                
            },
            'handlers':{
                'stage':[
                    {
                        'function': self.stage_post,
                        'scope': 'project'
                    },
                    {
                        'function': self.stage_personal_info,
                        'scope': 'global'
                    }
                ],
                'publish':[{
                    'function': self.publish,
                    'scope': 'global'
                }]
            },
            'apis':{
                'cli': self.cli
            }
        }

        self._staged_projects = []
            
        super().__init__(config, registry)

    @property
    def project_url(self, project: Project):
        return self.domain / project.name

    @property
    def posts_dir(self) -> Path:
        return Path(f"{self.env['dir']} / {self.env['posts_folder_name']}")

    @property
    def project_post_path(self, project: Project) -> Path:
        return Path(f"{self.posts_dir} / {project.date_created}-{project.name}.md")

    @property
    def project_media_dir(self, project: Project) -> Path:
        return Path(f"{self.env['dir']} / {self.env['media_folder_name'] / project.name}")

    @property
    def media_dir(self) -> Path:
        return Path(f"{self.env['dir']} / {self.env['media_folder_name']}")

    @property
    def pages_dir(self) -> Path:
        return Path(f"{self.env['dir']} / {self.env['pages_folder_name']}")

    @property
    def data_dir(self) -> Path:
        return Path(f"{self.env['dir']} / {self.env['data_folder_name']}")

    def cli(self):
        """Register CLI arguments needed by this integration."""
        # Use _add_argument which safely handles duplicates
        cli = self.registry.apis.get('cli')
        cli._add_argument('--commit-message', '-cm', default='', help='Commit message for any integration which commits to github')

    def get_media_files(self, project: Project, type):
        website_media_dir = self.project_media_dir / type
        media_files = []

        for file in website_media_dir.iterdir():
            media_files.append(f"/media/{project.name}/{type}/{file.name}")
                
    def setup(self, project: Project, **kwargs):
        self._setup_media_folders(project)

    def _setup_media_folders(self, project: Project):
        media_dir = self.project_media_dir
        os.mkdir(media_dir)

        for media in [Media.IMAGES, Media.VIDEOS, Media.MODELS, Media.EMBEDS]:
            os.mkdir(media_dir / str(media.TYPE))

    def rename_project(self, project: Project, new) -> None:
        # Rename media directory
        old_media_dir = self.project_media_dir
        new_media_dir = self.media_dir / new.name
        
        if old_media_dir.exists():
            old_media_dir.rename(new_media_dir)
        else:
            self.logger.warn(f"No media directory found at {old_media_dir.absolute()}. Creating...")
            self._setup_media_folders(project)
            self.project_media_dir.rename(new_media_dir)

    def remove(self, project: Project, **kwargs):
        Path(self.project_post_path).unlink()
        media_dir = self.project_media_dir
        if media_dir.exists():
            shutil.rmtree(self.project_media_dir)
        
    def publish(self, project: Project, **kwargs) -> None:

        commit_message = kwargs.get('commit_message', 'Update website content')
        """Publish website content for projects"""           
        os.chdir(self.website_dir)
        result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
        
        if result.stdout.strip():

            if self._staged_projects:
                commit_message = f"Updating content for {', '.join(self._staged_projects)}"
                self._staged_projects = []

            subprocess.run(['git', 'add', '.'], check=True)
            subprocess.run(['git', 'commit', '-m', commit_message], check=True)
            subprocess.run(['git', 'push', 'origin', 'main'], check=True)
            self.logger.info("Published website changes")
        else:
            self.logger.info("No changes to publish for website")

    def stage_personal_info(self):
        info = load_personal_info(self)

        info.pop('last_name', None)
        info.pop('email', None)
        info.pop('phone', None)
        info.pop('location', None)

        info = yaml.dump(info, default_flow_style=False, sort_keys=False, allow_unicode=True)

        with open(self.website_data_dir / 'personal_info.yml', 'w') as f:
            f.write(info)

    def stage_post(self, project: Project, **kwargs) -> str:
        self._stage_media(project)
        embed_content = self._stage_embed_content(project)
        
        post = self._generate_post(project, embed_content, **kwargs)
        with open(self.project_post_path, 'w') as f:
            f.write(post)

        self.logger.info(f"Successfully staged website content for {project.name}")

        self._staged_projects.append(project.name)

    def _stage_media(self, project: Project) -> None:
        try:
            output_dir = self.project_media_dir
            last_published = self.last_run('publish')

            for media in [Media.IMAGES, Media.VIDEOS, Media.MODELS, Media.EMBEDS]:
                media_files = project.local.get_media_files(media.TYPE)
                output_type_dir = output_dir / str(media.TYPE)

                if media_files:                    
                    for file in media_files:
                        file_name = str(file.name)
                        file_last_modified = datetime.fromtimestamp( os.path.getctime(file.absolute()) )

                        if file_last_modified > last_published:
                            self.logger.info(f"staging {file_name}")

                            cleanup_source = True
                            
                            if media.TYPE == Media.IMAGES.TYPE:
                                source_file = resize_image_file(self, file, 1920, 1080)
                            elif media.TYPE == Media.VIDEOS.TYPE:
                                source_file = convert_video_file(self, file, 'mp4')
                            elif media.TYPE == Media.MODELS.TYPE:
                                source_file = convert_model_file(self, file, 'glb')
                            else:
                                source_file = file
                                cleanup_source = False
                            
                            dest_path = output_type_dir / source_file.name

                            if dest_path.exists():
                                os.remove(dest_path)

                            shutil.copy2(source_file, dest_path)
                            
                            if cleanup_source:
                                source_file.unlink()
                        else:
                            self.logger.info(f"{file_name} not changed since last publish, skipping")

                
            self.logger.info(f"Successfully staged all website media files for {project.name}")
        except Exception as e:
            self.logger.error(f"Failed to stage media for {project.name}: {e}")
            raise

    def _stage_embed_content(self, project: Project):
        try:
            project_dir = project.local.path

            output_embed_dir = self.project_media_dir / Media.EMBEDS.TYPE

            embeds = {}

            for embed in project.media['embeds']:
                if embed['source'] and embed['type']:
                    source_file = Path(project_dir) / Path(embed['source'])
                    dest_path =  output_embed_dir / Path(embed['source']).name
                    embed_key = f"{embed['type']}_embeds"

                    if embed_key not in embeds:
                        embeds[embed_key] = []

                    embeds[embed_key].append(f"/media/{project.name}/{Media.EMBEDS.TYPE}/{Path(embed['source']).name}")

                    shutil.copy2(source_file, dest_path)

            self.logger.info(f"Successfully staged all embed files for {project.name}")

            return embeds
        except Exception as e:
            self.logger.error(f"Failed to stage embed files for {project.name}: {e}")
            raise

    def _generate_post(self, project: Project, embed_content, **kwargs) -> None:
        try:
            front_matter = {
                'layout': 'post',
                'date': project.date_created,
                'featured': project.website['feature_post'],
                'images':self.get_media_files(project.name, Media.IMAGES.TYPE),
                'videos':self.get_media_files(project.name, Media.VIDEOS.TYPE),
                'models':self.get_media_files(project.name, Media.MODELS.TYPE),
                'project': project,
                'featured_content': self._determine_featured_content(project)
            }

            front_matter = front_matter | self._determine_featured_content(project)

            post_content = "{% include post-content.html %}"

            post = f"---\n{yaml.dump(front_matter, default_flow_style=False, sort_keys=False, allow_unicode=True)}---\n{post_content}"
            self.logger.info(f"Successfully generated post for {project.name}")
            return post
        except Exception as e:
            self.logger.error(f"Failed to generate post for {project.name}: {e}")
            raise

    def _determine_featured_content(self, project: Project) -> Dict:
        featured_content = project.media['featured_content']
        if featured_content.get('type') == 'code':            
            source_file = project.local.project_path / Path(featured_content['source'])
            if source_file.exists():
                with open(source_file, 'r') as f:
                    lines = f.readlines()
                    start = featured_content.get('start_line')
                    end = featured_content.get('end_line')
                    code_snippet = ''.join(lines[start:end])

                return {
                    'featured_code': code_snippet,
                    'code_language': featured_content.get('language')
                }
        else:
            return {
                'featured_image': f"/media/{project.name}/{featured_content['source']}"
            }
