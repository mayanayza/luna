import markdown
from jinja2 import Template
from weasyprint import CSS, HTML

from script.src.config import Config
from script.src.constants import Files
from script.src.utils import (
    get_project_content,
    get_project_metadata,
    get_project_path,
    load_template,
    setup_logging,
    strip_emoji,
)


class PDFHandler:
    def __init__(self, config: Config):
        self.config = config
        self.logger = setup_logging(__name__)
                
        # Initialize Markdown converter
        self.md = markdown.Markdown(extensions=['extra', 'codehilite'])

    def create(self, name: str) -> None:
        """Generate a PDF for a project"""

        self.delete(name)

        project_dir = get_project_path(self, name)
        metadata = get_project_metadata(self, name)
        project = metadata['project']

        self.logger.info(f"Generating PDF for {name}")

        try:
            # Read content file
            content = get_project_content(self, name)
            # Convert markdown to HTML
            html_content = self.md.convert(content)

            specs = metadata['physical_specifications']
            
            dimensions = f"{specs['dimensions']['width']}{specs['dimensions']['unit']} w x {specs['dimensions']['height']}{specs['dimensions']['unit']} h x {specs['dimensions']['depth']}{specs['dimensions']['unit']} d"
            weight = f"{specs['weight']['value']} {specs['weight']['unit']}"
            materials = ", ".join(specs['materials'])

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

            # Prepare template data
            template_data = {
                'title': strip_emoji(project['display_name']).strip(),
                'description': project.get('description', ''),
                'date': project['date_created'],
                'website': f"{self.config.website_domain}/{name}",
                'dimensions': dimensions,
                'weight': weight,
                'materials': materials,
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
                'content': html_content,
            }

            template_html = load_template(self, Files.PDF_LAYOUT)
            template = Template(template_html)
            html_string = template.render(**template_data)

            # Load CSS
            css_content = load_template(self, Files.PDF_STYLE)
            css = CSS(string=css_content)

            # Generate PDF
            output_path = project_dir / f"{name}.pdf"
            HTML(string=html_string).write_pdf(
                output_path,
                stylesheets=[css],
            )

            self.logger.info(f"Successfully generated PDF for {name}")
            
        except Exception as e:
            self.logger.error(f"Failed to generate PDF for {name}: {e}")
            raise

    def delete(self, name: str) -> None:
        project_dir = get_project_path(self, name)

        try:
            pdf_path = project_dir / f"{name}.pdf"
            if pdf_path.exists():
                pdf_path.unlink()
                self.logger.info(f"Deleted PDF for {name}")
            
        except Exception as e:
            self.logger.error(f"Failed to delete PDF for {name}: {e}")
            raise

    def rename(self, old_name: str, new_name: str) -> None:
        self.delete(old_name)
        self.create(new_name)