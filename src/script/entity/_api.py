import sys
from abc import abstractmethod

from src.script.entity._base import EntityBase


class Api(EntityBase):
	def __init__(self, registry):
		super().__init__(registry)

	@abstractmethod
	def start(self):
		pass

	def command(self, args, integration_registry, project_registry):

		try:
		    if args.integrations is not None or args.all_integrations is not False:
		        target_integrations = args.integrations if args.integrations else [args.integration] if args.integration else None
		        target_projects = args.projects if args.projects else [args.project] if args.project else None
		        
		        integration_registry.command(
		            command=args.command,
		            integrations=target_integrations,
		            all_integrations=args.all_integrations,
		            projects=target_projects,
		            all_projects=args.all_projects,
		            **{k: v for k, v in vars(args).items() if k not in ['command', 'integrations', 'all_integrations', 'projects', 'all_projects', 'integration']}
		        )
		    else:
		        target_projects = args.projects if args.projects else [args.project] if args.project else None

		        project_registry.command(
		            command=args.command,
		            projects=target_projects,
		            all_projects=args.all_projects
		        )
		            
		except Exception as e:
		    self.logger.error(f"Operation failed: {e}")
		    sys.exit(1)
