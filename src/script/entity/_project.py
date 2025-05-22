from typing import Any, Dict

from src.script.constants import EntityType
from src.script.entity._base import EntityBase, StorableEntity
from src.script.registry._base import Registry


class Project(StorableEntity):

    def __init__(self, registry: Registry, name: str, title: str, emoji: str, **kwargs) -> None:    
        
        kwargs['name'] = name

        super().__init__(registry, **kwargs)

        self._title = title
        self._emoji = emoji

        self._db_additional_fields = {
            'emoji': emoji,
            'title': title
        }

        if self.data == {}:
            self.data = {
                'metadata': {
                    'primary_url_integration': 'website',
                    'status': 'backlog',
                    'priority': 0,
                    'tagline': '',
                    'notes': '',
                    'tags': []
                },
                'media': {
                    'embeds': [],
                    'featured': {
                        'type': 'image',
                        'source': '',
                        'language': '',
                        'start_line': 0,
                        'end_line': 0
                    }
                },
                'attributes': {
                    'physical': {
                        'dimensions': {
                            'width': '',
                            'height': '',
                            'depth': '',
                            'unit': ''
                        },
                        'weight': {
                            'value': '',
                            'unit': ''
                        },
                        'materials': []
                    },
                    'technical_requirements': {
                        'power': '',
                        'space': '',
                        'lighting': '',
                        'mounting': '',
                        'temperature_range': '',
                        'humidity_range': '',
                        'ventilation_needs': ''
                    },
                    'exhibition': {
                        'setup': {
                            'time_required': '',
                            'people_required': '',
                            'tools_required': [],
                            'instructions': []
                        },
                        'maintenance': {
                            'tasks': [],
                            'supplies_needed': []
                        },
                        'history': []
                    }
                }
            }

    @property
    def title(self):
        """Get the project title."""
        return self._title

    @title.setter
    def title(self, value):
        """Set the project title."""
        self._title = value

    @property
    def emoji(self):
        """Get the project emoji."""
        return self._emoji

    @emoji.setter
    def emoji(self, value):
        """Set the project emoji."""
        self._emoji = value
        
    @property
    def display_title(self):
        """Get the display title with emoji prefix if available."""
        if self.emoji:
            return f"{self.emoji} {self.title}"
        return self.title

    @property
    def metadata(self):
        """Get project metadata."""
        return self._data.get('metadata', {})

    def create(self) -> Dict[str, Any]:
        """Create a new project."""
        try:            
            # Initialize data structure matching project.yml schema
            
            self.logger.info(f"Created project {self.name}")
            return self
        except Exception as e:
            self.logger.error(f"Error creating project: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            raise

    def handle_add_integration(self, integration:EntityBase):
        pi_registry = self.registry.manager.get_by_name(EntityType.PROJECT_INTEGRATION)

        pi = pi_registry.add_pi(self.ref, integration.ref)
        pi.setup()
        self.logger.info(f"Added integration '{pi.name}' to project {self.name}")
        
        return pi

    def handle_remove_integration(self, integration:EntityBase):            
        pi_registry = self.registry.manager.get_by_name(EntityType.PROJECT_INTEGRATION)

        removed_name = pi_registry.remove_pi(self.ref, integration.ref)
        self.logger.info(f"Removed integration '{removed_name}' from project {self.name}")



    def handle_rename(self, new_name: str, new_title: str = None, new_emoji: str = None) -> Dict[str, Any]:
        """Rename this project."""
        try:
            old_name = self.name
            old_title = self.title
            old_emoji = self.emoji
            
            # Update properties
            self.name = new_name
            if new_title is not None:
                self.title = new_title
            if new_emoji is not None:
                self.emoji = new_emoji
            
            # Update registry name index
            self.registry.update_name_index(self, old_name)
            
            # Update all integrations
            pi_registry = self.registry.manager.get_by_name(EntityType.PROJECT_INTEGRATION)
            pi_registry.rename_pis_for_project(
                                project_ref=self.ref,
                                new_name=self.name,
                                new_title=self.title,
                                new_emoji=self.emoji,
                                old_name=old_name,
                                old_title=old_title,
                                old_emoji=old_emoji)
            
            # Save changes to DB
            self.db.upsert(EntityType.PROJECT, self)
            
            self.logger.info(f"Renamed project from {old_name} to {self.name}")
        except Exception as e:
            self.logger.error(f"Error renaming project: {e}")
            raise

    def handle_delete(self):
        """Delete this project."""
        try:
            # Remove all integrations
            pi_registry = self.registry.manager.get_by_name(EntityType.PROJECT_INTEGRATION)
            pi_registry.remove_pis_for_project(self.ref)
            
            # Delete from DB
            with self.db.transaction():
                table = getattr(self.db.dal, EntityType.PROJECT)
                self.db.dal(table.id == self.id).delete()
                
            # Unregister from registry
            self.registry.unregister_entity(self)
            
            self.logger.info(f"Deleted project {self.name}")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting project: {e}")
            raise
     
        return None

    # def __getattr__(self, name):
    #     """Allow direct attribute access to integrations by name."""
    #     # Only try to get integration if it's not a standard attribute
    #     integration = self.get_integration_by_name(name)
    #     if integration:
    #         return integration
        
    #     # Standard attribute lookup failed
    #     raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")