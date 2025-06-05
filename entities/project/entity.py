
from entities.base import Entity
from registries.base import Registry


class ProjectBase(Entity):

    def __init__(self, registry: Registry, **kwargs) -> None:    
        super().__init__(registry, **kwargs)

            # if self.data == {}:
        #     self.data = {
        #         'metadata': {
        #             'primary_url_integration': 'website',
        #             'status': 'backlog',
        #             'priority': 0,
        #             'tagline': '',
        #             'notes': '',
        #             'tags': []
        #         },
        #         'media': {
        #             'embeds': [],
        #             'featured': {
        #                 'type': 'image',
        #                 'source': '',
        #                 'language': '',
        #                 'start_line': 0,
        #                 'end_line': 0
        #             }
        #         },
        #         'attributes': {
        #             'physical': {
        #                 'dimensions': {
        #                     'width': '',
        #                     'height': '',
        #                     'depth': '',
        #                     'unit': ''
        #                 },
        #                 'weight': {
        #                     'value': '',
        #                     'unit': ''
        #                 },
        #                 'materials': []
        #             },
        #             'technical_requirements': {
        #                 'power': '',
        #                 'space': '',
        #                 'lighting': '',
        #                 'mounting': '',
        #                 'temperature_range': '',
        #                 'humidity_range': '',
        #                 'ventilation_needs': ''
        #             },
        #             'exhibition': {
        #                 'setup': {
        #                     'time_required': '',
        #                     'people_required': '',
        #                     'tools_required': [],
        #                     'instructions': []
        #                 },
        #                 'maintenance': {
        #                     'tasks': [],
        #                     'supplies_needed': []
        #                 },
        #                 'history': []
        #             }
        #         }
        #     }