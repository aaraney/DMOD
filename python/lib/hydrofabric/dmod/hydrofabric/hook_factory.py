from typing import List, Type, TypeVar
from functools import partial

from .hook_fulfillment import Hook, HookFulfillment

from ngen.init_config import Base

M = TypeVar("M", bound=Base)


def hook_factory(m: Type[M], hook_data: List[HookFulfillment]) -> partial[M]:
    if not hook_data:
        raise ValueError("one of more `hook_data` required.")

    for hd in hook_data:
        if not issubclass(m, hd.hook.type):
            raise RuntimeError(f"{m!r} does not implement hook, {hd.hook.name!r}")

        if hd.hook == Hook.HydrofabricCatchment:
            fn = partial(m.hydrofabric_catchment_hook, **hd.data)

        elif hd.hook == Hook.ForcingMetadata:
            fn = partial(m.forcing_metadata_hook, **hd.data)

        elif hd.hook == Hook.Realization:
            fn = partial(m.realization_hook, **hd.data)

        else:
            raise RuntimeError("unreachable")

    return fn
