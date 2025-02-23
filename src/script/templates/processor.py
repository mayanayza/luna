import os
from pathlib import Path
from typing import Dict

from jinja2 import Environment, FileSystemLoader
from src.script.config import Config
from src.script.constants import Status
from src.script.utils import (
    get_project_content,
    get_project_metadata,
    get_project_readme,
    is_public_github_repo,
    setup_logging,
)


class TemplateProcessor:
    def __init__(self, config: Config):
        self.config = config
        current_dir = Path(__file__).parent
        self.logger = setup_logging(__name__)
        self.env = Environment(
            loader=FileSystemLoader(current_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        
        def basename(path):
            return os.path.basename(path)

        self.env.filters['basename'] = basename
        
    def process_github_readme_template(self, name, context):
        template = self.env.get_template('github/README.md')
        return template.render(context)

    def process_pdf_cover_template(self, context):
        template = self.env.get_template('pdf/cover.html')
        return template.render(context)

    def process_pdf_project_template(self, name, context):
        template = self.env.get_template('pdf/project.html')
        return template.render(context)

    def process_pdf_images_template(self, name, context):
        template = self.env.get_template('pdf/project_images.html')
        return template.render(context)

    def get_post_template(self):
        with open(f'{Path(__file__).parent}/web/post.md', 'r') as file:
            return file.read()

    def get_roadmap_template(self):
        with open(f'{Path(__file__).parent}/web/roadmap.md', 'r') as file:
            return file.read()

    def get_links_template(self):
        with open(f'{Path(__file__).parent}/web/links.md', 'r') as file:
            return file.read()

    def process_about_template(self, context):
        template = self.env.get_template('web/about.md')
        return template.render(context)

    def process_project_metadata(self, name: str) -> Dict:
        
        try:
            processed = {}
            metadata = get_project_metadata(self, name)
            project = metadata['project']

            processed['website'] = self.config.website_domain
            processed['github'] = self.config.github_url_path
            processed['github_username'] = self.config.github_username

            if (project['status'] == Status.COMPLETE):
                project['website'] = f"{self.config.website_domain}/{name}"
            if is_public_github_repo(self, name):
                project['github'] = f"{self.config.github_url_path}/{name}"

            project['written_content'] = get_project_content(self, name)
            project['readme'] = get_project_readme(self, name)

            processed['project'] = project

            specs = metadata['physical_specifications']
                
            if (specs['dimensions']['width'] and specs['dimensions']['height'] and specs['dimensions']['depth']):
                processed['dimensions'] = f"{specs['dimensions']['width']}{specs['dimensions']['unit']} w x {specs['dimensions']['height']}{specs['dimensions']['unit']} h x {specs['dimensions']['depth']}{specs['dimensions']['unit']} d"

            if specs['weight']['value']:
                processed['weight'] = f"{specs['weight']['value']} {specs['weight']['unit']}"
            
            if specs['materials']:
                processed['materials'] = ", ".join(specs['materials'])

            
            reqs = metadata['technical_requirements']
            for key in reqs:
                if reqs[key]:
                    processed[key] = reqs[key]

            ex = metadata['exhibition']

            if ex['setup']['instructions']:
                processed['setup_instructions'] = ex['setup']['instructions']
            
            if ex['setup']['time_required']:
                processed['setup_time'] = ex['setup']['time_required']

            if ex['setup']['people_required']:
                processed['setup_people'] = ex['setup']['people_required']
            
            if ex['setup']['tools_required']:
                processed['setup_tools'] = ", ".join(ex['setup']['tools_required'])

            if ex['maintenance']['supplies_needed']:
                processed['maintenance_supplies'] = ", ".join(ex['maintenance']['supplies_needed'])
            
            if ex['maintenance']['tasks']:
                processed['maintenance_instructions'] = ex['maintenance']['tasks']

            self.logger.debug(f"Processed metadata for {name}")
            return processed

        except Exception as e:
            self.logger.error(f"Failed to process metadata for {name}: {e}")
            raise

        

