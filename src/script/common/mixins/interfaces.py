from abc import ABC, abstractmethod


class InterfaceMixin(ABC):
    pass


class ListableMixin(InterfaceMixin):
    pass


class CreatableMixin(InterfaceMixin):
    pass


class NameableMixin(InterfaceMixin):
    pass


class CreatableFromModuleMixin(InterfaceMixin):

    @property
    @classmethod
    @abstractmethod
    def package(self) -> str:
        pass
