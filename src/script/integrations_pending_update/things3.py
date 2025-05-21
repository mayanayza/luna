import subprocess

from src.script.integration._integration import Integration
from src.script.integration._registry import IntegrationRegistry
from src.script.project._project import Project


class Things3Integration(Integration):
	def __init__(self, registry: IntegrationRegistry):
		config = {
		    'name': 'things3',
		    'env': {
		    	'area':'THINGS3_AREA'
		    },
		    'project_fields':{},
		    'handlers':{},
			'apis':{}
		}

		super().__init__(config, registry)


	def setup(self, project: Project, **kwargs):
		display_name = project['project']['display_name']

		applescript = f'''
		tell application "Things3"
		    set newProject to make new project with properties {{{{name:"{display_name}"}}}}
		    set newProject's area to area "{self.things3_area}"
		end tell
		'''
		try:
		    subprocess.run(['osascript', '-e', applescript], check=True)
		    self.logger.info(f"Created Things 3 project: {display_name}")
		except subprocess.CalledProcessError as e:
		    self.logger.error(f"Failed to create Things 3 project: {e}")

	def remove(self, project: Project, **kwargs):
		print('TODO: Implement things delete functionality')

	def rename(self, project: Project, new) -> None:
	    """Rename a project in Things 3"""
	    new_display_name = new.display_name
	    old_display_name = project['project']['display_name']

	    applescript = f'''
	    tell application "Things3"
	        set oldProject to first project whose name = "{old_display_name}"
	        set oldProject's name to "{new_display_name}"
	    end tell
	    '''
	    try:
	        subprocess.run(['osascript', '-e', applescript], check=True)
	        self.logger.info(f"Renamed Things 3 project from '{old_display_name}' to '{new_display_name}'")
	    except subprocess.CalledProcessError as e:
	        self.logger.error(f"Failed to rename Things 3 project: {e}")
