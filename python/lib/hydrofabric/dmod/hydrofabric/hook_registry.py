from typing import (
    Dict,
    Iterable,
    Literal,
    ItemsView,
    List,
    Type,
    Tuple,
    Union,
    overload,
)
from .hooks import (
    Hook,
    HookT,
    HydrofabricCatchmentHook,
    RealizationHook,
    ForcingMetadataHook,
)


class HookRegistry:
    def __init__(self):
        # mapping of some T and all the hooks T implements
        self._registered: Dict[HookT, List[Hook]] = {}

    def __contains__(self, other: HookT) -> bool:
        return other in self.registered

    def __iter__(self) -> Iterable[HookT]:
        yield from self.registered

    def __getitem__(self, other: HookT) -> List[Hook]:
        return self.registered[other].copy()

    def __len__(self) -> int:
        return len(self.registered)

    def __str__(self) -> str:
        return str(self.registered.items())

    def items(self) -> ItemsView[HookT, List[Hook]]:
        return self.registered.items()

    @overload
    def types_with_hook(
        self, hook: Literal[Hook.HydrofabricCatchment]
    ) -> List[Type[HydrofabricCatchmentHook]]:
        ...

    @overload
    def types_with_hook(
        self, hook: Literal[Hook.Realization]
    ) -> List[Type[RealizationHook]]:
        ...

    @overload
    def types_with_hook(
        self, hook: Literal[Hook.ForcingMetadata]
    ) -> List[Type[ForcingMetadataHook]]:
        ...

    def types_with_hook(
        self, hook: Hook
    ) -> Union[
        List[Type[HydrofabricCatchmentHook]],
        List[Type[RealizationHook]],
        List[Type[ForcingMetadataHook]],
    ]:
        ts: List[Hook] = []

        for t, hooks in self.items():
            if hook in hooks:
                ts.append(t)

        return ts

    def register(self, *ts: HookT) -> None:
        for t in ts:
            t_hooks: List[Hook] = []
            for hook in Hook:
                if issubclass(t, hook.type):
                    t_hooks.append(hook)

            if not t_hooks:
                continue

            self._registered[t] = t_hooks

    @property
    def requirements(self) -> Tuple[Hook]:
        return tuple({r for t_hooks in self.registered.values() for r in t_hooks})

    @property
    def registered(self) -> Dict[HookT, List[Hook]]:
        return self._registered
