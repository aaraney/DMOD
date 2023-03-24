from dataclasses import dataclass
from typing import Any, Dict, Literal, Union, overload
from typing_extensions import Self

from ngen.init_config import Base
from .hooks import Hook


@dataclass
class HookFulfillment:
    hook: Hook
    data: Dict[str, Any]

    @overload
    @classmethod
    def create(
        cls,
        *,
        hook: Literal[Hook.HydrofabricCatchment],
        data: Dict[str, Dict[str, Any]],
    ) -> Self:
        ...

    @overload
    @classmethod
    def create(cls, *, hook: Literal[Hook.Realization], data: Base) -> Self:
        ...

    @overload
    @classmethod
    def create(cls, *, hook: Literal[Hook.ForcingMetadata], data: Base) -> Self:
        ...

    @classmethod
    def create(
        cls, *, hook: Hook, data: Union[Base, Dict[str, Dict[str, Any]]]
    ) -> Self:
        return cls(hook=hook, data=data)
