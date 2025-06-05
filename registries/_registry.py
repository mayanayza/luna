from registries.base import Registry
from registries._loader import RegistryLoaderFactory



# class ListableEntityRegistry(Registry):
#     def __init__(self, service_class, manager):
#
#         self.module_loader = RegistryLoaderFactory.create_module_loader(self)
#         self.database_loader = None
#
#         super().__init__(service_class, manager)
        
# class CreatableEntityRegistry(ListableEntityRegistry):
#     def __init__(self, service_class, manager):
#
#         super().__init__(service_class, manager)
#
#         self.module_loader = None
#         self.database_loader = RegistryLoaderFactory.create_database_loader(self)
#
#         self._db_ref = self.manager.db_ref
#
#     @property
#     def db(self):
#         if not hasattr(self, '_db_ref') or self._db_ref is None:
#             raise RuntimeError(f"Database reference not set for {self.__class__.__name__}")
#         else:
#             return self.manager.get_entity_by_ref(self._db_ref)
#
#     @db.setter
#     def db(self, db_ref):
#         self._db_ref = db_ref
#
#         for entity in self._entities.values():
#             entity.db = db_ref
#
#     def register_entity(self, entity):
#         super().register_entity(entity)
#         entity.db = self._db_ref
            
# class NameableEntityRegistry(CreatableEntityRegistry):
#     def __init__(self, service_class, manager):
#         super().__init__(service_class, manager)
#
#         self.database_loader = RegistryLoaderFactory.create_database_loader(self)
#         self.module_loader = None
#
#         self.database_loader.load(self.entity_type.value)

# class CreatableFromModuleEntityRegistry(NameableEntityRegistry):
#
#     package: str = NotImplemented # Will come from entity mixin
#
#     def __init__(self, service_class, manager):
#         super().__init__(service_class, manager)
#
#         self.database_loader = RegistryLoaderFactory.create_database_loader(self)
#         self.module_loader = RegistryLoaderFactory.create_module_loader(self)
#
#         entity_data = self.database_loader.fetch_raw_data(self.entity_type.value)
#
#         for data in entity_data:
#             self.module_loader.load(f'{self.package}.{data['module_name']}', **data)
#
#     def list_modules(self):
#         return self.module_loader.get_module_filenames(self.package)