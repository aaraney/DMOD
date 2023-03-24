from enum import Enum
from functools import partial
from typing import Any, Dict, Protocol, Type, Union, runtime_checkable
from typing_extensions import Self, TypeAlias

from ngen.init_config import Base


@runtime_checkable
class HydrofabricCatchmentHook(Protocol):
    @classmethod
    def hydrofabric_catchment_hook(
        cls: Type[Self], link_data: Dict[str, Dict[str, Any]]
    ) -> partial[Self]:
        ...


@runtime_checkable
class RealizationHook(Protocol):
    @classmethod
    def realization_hook(cls: Type[Self], realization: Base) -> partial[Self]:
        ...


@runtime_checkable
class ForcingMetadataHook(Protocol):
    @classmethod
    def forcing_metadata_hook(cls: Type[Self], forcing_metadata: Base) -> partial[Self]:
        ...


HookT: TypeAlias = Union[
    Type[HydrofabricCatchmentHook], Type[RealizationHook], Type[ForcingMetadataHook]
]


class Hook(Enum):
    HydrofabricCatchment = (HydrofabricCatchmentHook,)
    Realization = (RealizationHook,)
    ForcingMetadata = (ForcingMetadataHook,)

    @property
    def type(self) -> HookT:
        return self.value[0]


# from typing import Protocol, Generic, TypeVar, Type, Tuple, Iterator
# from typing_extensions import Self

# T = TypeVar("T", covariant=True)


# class HookProto(Protocol, Generic[T]):
#     @property
#     def type(self) -> T:
#         ...

#     def __iter__(self) -> Iterator[Self]:
#         ...


# def foo(hp: HookProto[T], *, __a: T = None):
#     ...


# foo(Hook)

# add_catchment_formulation(id: str, formulation: Formulation, forcing: Optional[Forcing])
# add_global_formulation(formulation: Formulation, forcing: Forcing)
# add_time(time: Time)
# add_hydrofabric(...)
