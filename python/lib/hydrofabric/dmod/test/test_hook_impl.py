from ..hydrofabric.hook_registry import HookRegistry
from ..hydrofabric.hooks import Hook
from ..hydrofabric.hook_fulfillment import HookFulfillment
from ..hydrofabric.hook_factory import hook_factory
from ..hydrofabric.linked_data_provider import GPKGLinkedDataProvider

from . import hydrofabric_fixture
from functools import partial
from pydantic import root_validator
from typing import (
    Any,
    Dict,
    List,
    Type,
    TypeVar,
)
from typing_extensions import Self
from ngen.init_config import Base
from .pet import PET

# verbose=0
# run_unit_tests=0

# pet_method=5
# forcing_file=BMI
# yes_aorc=1 ; if BMI, is implied to be True?
# yes_wrf=0
# wind_speed_measurement_height_m=10.0 ; if aorc, can this be implied as 10m?  per page 4 of
# ; https://hydrology.nws.noaa.gov/aorc-historic/Documents/AORC-Version1.1-SourcesMethodsandVerifications.pdf,
# ; it seems so
# humidity_measurement_height_m=2.0
# cloud_base_height_known=FALSE
# time_step_size_s=3600
# num_timesteps=720
# shortwave_radiation_provided=0

# vegetation_height_m=0.12
# zero_plane_displacement_height_m=0.0003
# momentum_transfer_roughness_length=0.0
# heat_transfer_roughness_length_m=0.0
# surface_longwave_emissivity=1.0
# surface_shortwave_albedo=0.22

# latitude_degrees=37.25
# longitude_degrees=-97.5554
# site_elevation_m=303.33


class PetWithHooks(PET):
    @root_validator(pre=True)
    def _validate(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if not bool(values["yes_aorc"]):
            return values
        values["yes_wrf"] = False
        values["wind_speed_measurement_height_m"] = 10.0
        values["humidity_measurement_height_m"] = 10.0
        values["shortwave_radiation_provided"] = False
        values["time_step_size_s"] = 3600
        values["num_timesteps"] = 720
        values["cloud_base_height_known"] = False
        return values

    @classmethod
    def hydrofabric_catchment_hook(
        cls: Type[Self], link_data: Dict[str, Dict[str, Any]]
    ) -> partial[Self]:
        # NOTE typo in forcing metadata name
        longitude_degrees = link_data["forcing_metadata"]["cetroid_lon"]
        latitude_degrees = link_data["forcing_metadata"]["centroid_lat"]
        site_elevation_m = link_data["forcing_metadata"]["elevation"]
        return partial(
            cls,
            longitude_degrees=longitude_degrees,
            latitude_degrees=latitude_degrees,
            site_elevation_m=site_elevation_m,
        )

    # @classmethod
    # def realization_hook(cls: Type[Self], realization: Base) -> Self:
    #     ...

    # @classmethod
    # def forcing_metadata_hook(cls: Type[Self], forcing_metadata: Base) -> Self:
    #     ...


T = TypeVar("T")


def test_generate():
    cat_id = "cat-1"
    with hydrofabric_fixture() as connection:
        o = GPKGLinkedDataProvider(connection=connection)
        cat_data = o.get_data(cat_id)

    partial_config = PetWithHooks.hydrofabric_catchment_hook(cat_data)

    # several of these come from land cover data, it is just unclear what land cover data is to be used
    data = {
        "yes_aorc": True,
        "pet_method": 5,
        "vegetation_height_m": 0.12,
        "zero_plane_displacement_height_m": 0.0003,
        "momentum_transfer_roughness_length": 0.0,
        "heat_transfer_roughness_length_m": 0.0,
        "surface_longwave_emissivity": 1.0,
        "surface_shortwave_albedo": 0.22,
    }
    config = partial_config(**data)
    # print(config)


# two flows:
# formulation per catchment
# global formulation


def test_it():
    models = [PetWithHooks]
    registry = HookRegistry()
    registry.register(*models)

    required_hooks = registry.requirements

    with hydrofabric_fixture() as connection:
        o = GPKGLinkedDataProvider(connection=connection)
        catchments = o.catchment_ids()

    catchment_hook_reqs: Dict[str, Dict[Hook, HookFulfillment]] = {}

    for id in catchments:
        hook_data: Dict[Hook, HookFulfillment] = {}

        for req in required_hooks:
            if req == Hook.HydrofabricCatchment:
                with hydrofabric_fixture() as connection:
                    o = GPKGLinkedDataProvider(connection=connection)
                    data = o.get_data(id)
                    hook_data[req] = HookFulfillment.create(hook=req, data=data)

            elif req == Hook.ForcingMetadata:
                ...

            elif req == Hook.Realization:
                ...

            else:
                raise RuntimeError("unreachable")

        if hook_data:
            catchment_hook_reqs[id] = hook_data

    cat_partial_configs: Dict[str, List[Base]] = {}
    for id, hook_fulfillment_map in catchment_hook_reqs.items():
        partial_configs: List[partial[Base]] = []
        for model, model_hooks in registry.items():
            assert issubclass(model, Base)
            partial_config = hook_factory(
                model, [hook_fulfillment_map[hook] for hook in model_hooks]
            )

            partial_configs.append(partial_config)

        cat_partial_configs[id] = partial_configs
