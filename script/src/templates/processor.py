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
            metadata = get_project_metadata(self, name)
            
            project = metadata['project']

            if (project['status'] == Status.COMPLETE):
                project['website'] = f"{self.config.website_domain}/{name}"
            if is_public_github_repo(self, name):
                project['github'] = f"{self.config.github_url_path}/{name}"

            specs = metadata['physical_specifications']
                
            dimensions = f"{specs['dimensions']['width']}{specs['dimensions']['unit']} w x {specs['dimensions']['height']}{specs['dimensions']['unit']} h x {specs['dimensions']['depth']}{specs['dimensions']['unit']} d"
            weight = f"{specs['weight']['value']} {specs['weight']['unit']}"
            
            materials = specs['materials']['primary']
            consumables = specs['materials']['consumables']

            materials = ", ".join(materials)
            consumables = ", ".join(materials)

            reqs = metadata['technical_requirements']

            lighting = reqs['lighting']
            mounting = reqs['mounting']
            temperature_range = reqs['environmental']['temperature_range']
            humidity_range = reqs['environmental']['humidity_range']
            ventilation_needs = reqs['environmental']['ventilation_needs']

            ex = metadata['exhibition']

            setup_instructions = ex['setup']['instructions']
            setup_time = ex['setup']['time_required']
            setup_people = ex['setup']['people_required']
            setup_tools = ", ".join(ex['setup']['tools_required'])

            maintenance_supplies = ", ".join(ex['maintenance']['supplies_needed'])
            maintenance_instructions = ex['maintenance']['tasks']

            processed = {
                'project': project,
                'dimensions': dimensions,
                'weight': weight,
                'materials': materials,
                'consumables': consumables,
                'lighting': lighting,
                'mounting': mounting,
                'temperature_range': temperature_range,
                'humidity_range': humidity_range,
                'ventilation_needs': ventilation_needs,
                'setup_instructions': setup_instructions,
                'setup_time': setup_time,
                'setup_tools': setup_tools,
                'setup_people': setup_people,
                'maintenance_supplies': maintenance_supplies,
                'maintenance_instructions': maintenance_instructions,
            }

            return processed

        except Exception as e:
            self.logger.error(f"Failed to process metadata readme for {name}: {e}")
            raise

        

