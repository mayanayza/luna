from pathlib import Path
from typing import Dict

from jinja2 import Environment, FileSystemLoader, Template
from script.src.config import Config
from script.src.constants import Status
from script.src.utils import (
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
            lstrip_blocks=True
        )

    def process_template(self, name: str, template_name: str, context: Dict={}):
        try:
            context_cleaned = {}

            context = context | self.process_project_metadata(name)
            # Remove empty values
            for key, value in context.items():
                if value not in ([], '', None):
                    context_cleaned[key] = value

            content = get_project_content(self, name)
            if content:
                content = Template( str(content) ).render(context)
                context_cleaned['content'] = content

            readme = get_project_readme(self, name)
            if readme:
                readme = Template( str(readme) ).render(context)
                context_cleaned['readme'] = readme
            
            template = self.env.get_template(template_name)
            rendered = template.render(context_cleaned)
            return rendered
        except Exception as e:
            self.logger.error(f"Failed to process template for {name}: {e}")
            raise
        
    def process_project_metadata(self, name: str) -> Dict:
        
        try:
            processed = {}
            metadata = get_project_metadata(self, name)
            project = metadata['project']

            processed['website'] = self.config.website_domain
            processed['github'] = self.config.github_url_path

            if (project['status'] == Status.COMPLETE):
                project['website'] = f"{self.config.website_domain}/{name}"
            if is_public_github_repo(self, name):
                project['github'] = f"{self.config.github_url_path}/{name}"

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
                processed['setup_tools'] = ex['setup']['people_required']
            
            if ex['setup']['tools_required']:
                processed['setup_people'] = ", ".join(ex['setup']['tools_required'])

            if ex['maintenance']['supplies_needed']:
                processed['maintenance_supplies'] = ", ".join(ex['maintenance']['supplies_needed'])
            
            if ex['maintenance']['tasks']:
                processed['maintenance_instructions'] = ex['maintenance']['tasks']

            self.logger.info(f"Processed metadata for {name}")
            return processed

        except Exception as e:
            self.logger.error(f"Failed to process metadata for {name}: {e}")
            raise

        

