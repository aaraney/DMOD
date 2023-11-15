# TODO: check when runtime_checkable was introduced
from typing import (
    Any,
    Callable,
    Collection,
    Dict,
    Iterable,
    Literal,
    Protocol,
    Union,
    runtime_checkable,
)
from pathlib import Path
from enum import Enum
import warnings
from typing_extensions import Self
from pydantic import BaseModel

from ngen.init_config.serializer import (
    IniSerializer,
    JsonSerializer,
    NamelistSerializer,
    TomlSerializer,
    YamlSerializer,
)

from ngen.config.init_config.pet import PET, PetMethod

import pandas as pd
import geopandas as gpd


@runtime_checkable
class Builder(Protocol):
    def build(self) -> BaseModel:
        ...


@runtime_checkable
class Visitable(Protocol):
    def visit(self, hook_provider: "HookProvider") -> None:
        ...


@runtime_checkable
class BuilderVisitable(Builder, Visitable, Protocol):
    pass


# TODO: determine if this is an appropriate name. See what id's are referenced
# in the linked data (divides id?)
@runtime_checkable
class HydrofabricHook(Protocol):
    """
    v2.0 Hydrofabric data schema:
        divide_id                     str
        areasqkm                    float
        toid                          str
        type                          str
        ds_id                       float
        id                            str
        lengthkm                    float
        tot_drainage_areasqkm       float
        has_flowline                 bool
        geometry                 geometry
    """

    def hydrofabric_hook(
        self, version: str, divide_id: str, data: Dict[str, Any]
    ) -> None:
        ...


# TODO: determine if this is an appropriate name. See what id's are referenced
# in the linked data (divides id?)
@runtime_checkable
class HydrofabricLinkedDataHook(Protocol):
    """
    v2.0 Hydrofabric linked data schema:
        divide_id                        str
        elevation_mean                 float
        slope_mean                     float
        impervious_mean                float
        aspect_c_mean                  float
        twi_dist_4                       str
        X                              float
        Y                              float
        gw_Coeff                       float
        gw_Zmax                        float
        gw_Expon                       float
        bexp_soil_layers_stag=1        float
        bexp_soil_layers_stag=2        float
        bexp_soil_layers_stag=3        float
        bexp_soil_layers_stag=4        float
        ISLTYP                           int
        IVGTYP                           int
        dksat_soil_layers_stag=1       float
        dksat_soil_layers_stag=2       float
        dksat_soil_layers_stag=3       float
        dksat_soil_layers_stag=4       float
        psisat_soil_layers_stag=1      float
        psisat_soil_layers_stag=2      float
        psisat_soil_layers_stag=3      float
        psisat_soil_layers_stag=4      float
        cwpvt                          float
        mfsno                          float
        mp                             float
        quartz_soil_layers_stag=1      float
        quartz_soil_layers_stag=2      float
        quartz_soil_layers_stag=3      float
        quartz_soil_layers_stag=4      float
        refkdt                         float
        slope                          float
        smcmax_soil_layers_stag=1      float
        smcmax_soil_layers_stag=2      float
        smcmax_soil_layers_stag=3      float
        smcmax_soil_layers_stag=4      float
        smcwlt_soil_layers_stag=1      float
        smcwlt_soil_layers_stag=2      float
        smcwlt_soil_layers_stag=3      float
        smcwlt_soil_layers_stag=4      float
        vcmx25                         float
    """

    def hydrofabric_linked_data_hook(
        self, version: str, divide_id: str, data: Dict[str, Any]
    ) -> None:
        ...


@runtime_checkable
class HookProvider(Protocol):
    def provide_hydrofabric_data(self, hook: HydrofabricHook):
        ...

    def provide_hydrofabric_linked_data(self, hook: HydrofabricLinkedDataHook):
        ...


class DefaultHookProvider(HookProvider):
    def __init__(self, hf: gpd.GeoDataFrame, hf_lnk_data: pd.DataFrame):
        self.__hf = hf.sort_values("divide_id")
        self.__hf_lnk = hf_lnk_data.sort_values("divide_id")

        # TODO: should this be a warning?
        assert len(self.__hf) == len(
            self.__hf_lnk
        ), "hydrofabric and hydrofabric link data have differing number of records"

        self.hf_iter = self.__hf.iterrows()
        self.hf_lnk_iter = self.__hf_lnk.iterrows()

        self.hf_row: Union[Dict[str, Any], None] = None
        self.hf_lnk_row: Union[Dict[str, Any], None] = None

    def provide_hydrofabric_data(self, hook: HydrofabricHook):
        if self.hf_row is None:
            raise RuntimeError("hook provider has no data")
        # TODO: figure out how to get this
        version = "2.0"
        divide_id = self.hf_row["divide_id"]

        hook.hydrofabric_hook(version, divide_id, self.hf_row)

    def provide_hydrofabric_linked_data(self, hook: HydrofabricLinkedDataHook):
        if self.hf_lnk_row is None:
            raise RuntimeError("hook provider has no data")
        # TODO: figure out how to get this
        version = "2.0"
        divide_id = self.hf_lnk_row["divide_id"]

        hook.hydrofabric_linked_data_hook(version, divide_id, self.hf_lnk_row)

    def __iter__(self) -> Self:
        return self

    def __next__(self):
        # NOTE: StopIteration will be raised when next can no longer be called.
        # this should always be the _first_ iterator.
        # If length of iterator guarantee changes, this will also need to change.
        _, hf_row = next(self.hf_iter)
        self.hf_row = hf_row.to_dict()
        _, hf_lnk_row = next(self.hf_lnk_iter)
        self.hf_lnk_row = hf_lnk_row.to_dict()
        return self


class DivideIdHookObject:
    def __init__(self):
        self.__divide_id: Union[str, None] = None

    def hydrofabric_hook(
        self, version: str, divide_id: str, data: Dict[str, Any]
    ) -> None:
        self.__divide_id = divide_id

    def visit(self, hook_provider: "HookProvider") -> None:
        hook_provider.provide_hydrofabric_data(self)

    def divide_id(self) -> Union[str, None]:
        return self.__divide_id


class FileWriter(Protocol):
    def __call__(self, id: Union[str, Literal["global"]], data: BaseModel):
        ...


class DefaultFileWriter:
    def __init__(self, root: Union[str, Path]):
        root = Path(root)
        if not root.exists():
            root.mkdir(parents=True)
        elif root.is_file():
            raise FileExistsError(f'expected dir got file: "{root!s}"')
        self.__root = root

    @staticmethod
    def _get_serializer(data: BaseModel) -> Callable[[Path], None]:
        def json_serializer(m: BaseModel):
            def serialize(p: Path):
                p.write_text(m.json())

            return serialize

        if isinstance(data, IniSerializer):
            return data.to_ini
        elif isinstance(data, JsonSerializer):
            return data.to_json
        elif isinstance(data, NamelistSerializer):
            return data.to_namelist
        elif isinstance(data, TomlSerializer):
            return data.to_toml
        elif isinstance(data, YamlSerializer):
            return data.to_yaml
        elif isinstance(data, BaseModel):
            json_serializer(data)

        raise RuntimeError(f'unaccepted type: "{type(data)}"')

    @staticmethod
    def _get_file_extension(data: BaseModel) -> str:
        if isinstance(data, IniSerializer):
            return "ini"
        elif isinstance(data, JsonSerializer):
            return "json"
        elif isinstance(data, NamelistSerializer):
            return "namelist"
        elif isinstance(data, TomlSerializer):
            return "toml"
        elif isinstance(data, YamlSerializer):
            return "yaml"
        elif isinstance(data, BaseModel):
            return "json"

        raise RuntimeError(f'unaccepted type: "{type(data)}"')

    @staticmethod
    def _gen_alt_filename(p: Path) -> Path:
        stem = p.stem
        ext = p.suffix
        f_name = p
        i = 1
        while f_name.exists():
            f_name = p.with_name(f"{stem}_{i:02}{ext}")
            i += 1
        return f_name

    def __call__(self, id: Union[str, Literal["global"]], data: BaseModel):
        class_name = data.__class__.__name__
        ext = DefaultFileWriter._get_file_extension(data)
        output_file = self.__root / f"{class_name}_{id}.{ext}"

        if output_file.exists():
            alt_name = DefaultFileWriter._gen_alt_filename(output_file)
            warnings.warn(
                f'"{output_file!s}" already exists; writing to "{alt_name!s}" instead'
            )
            output_file = alt_name

        serializer = DefaultFileWriter._get_serializer(data)
        serializer(output_file)


class BuilderVisitableFn(Protocol):
    def __call__(self) -> BuilderVisitable:
        ...


# NOTE: not happy with the name of this... think more about it
class Context(str, Enum):
    GLOBAL = "global"
    LOCAL = "local"


def generate_configs(
    hook_providers: Iterable[HookProvider],
    hook_objects: Collection[BuilderVisitableFn],
    file_writer: FileWriter,
):
    div_hook_obj = DivideIdHookObject()
    for hook_prov in hook_providers:
        # retrieve current divide id
        div_hook_obj.visit(hook_prov)
        divide_id = div_hook_obj.divide_id()
        assert divide_id is not None

        for v_fn in hook_objects:
            bld_vbl = v_fn()
            bld_vbl.visit(hook_prov)
            model = bld_vbl.build()
            file_writer(divide_id, model)


class PetHooks:
    def __init__(self):
        self.data = {}
        self.__version = None

    def _set_version(self, version: str):
        if self.__version is None:
            self.__version = version
        elif self.__version != version:
            raise RuntimeError(
                f'mismatched versions. current="{self.__version}" new="{version}"'
            )

    def _version(self) -> str:
        if self.__version is None:
            raise RuntimeError("no version set")
        return self.__version

    def _v2_linked_data_hook(self, data: Dict[str, Any]):
        # NOTE typo in forcing metadata name
        self.data["longitude_degrees"] = data["X"]
        self.data["latitude_degrees"] = data["Y"]
        self.data["site_elevation_m"] = data["elevation_mean"]

    def hydrofabric_linked_data_hook(
        self, version: str, divide_id: str, data: Dict[str, Any]
    ) -> None:
        self._set_version(version)
        if self._version() == "2.0":
            self._v2_linked_data_hook(data)
        else:
            raise RuntimeError("only support v2 hydrofabric")

    def _v2_defaults(self) -> None:
        # TODO: this was from old code, not sure what to do here
        # if not bool(values["yes_aorc"]):
        #     return values
        self.data["yes_wrf"] = False
        self.data["wind_speed_measurement_height_m"] = 10.0
        self.data["humidity_measurement_height_m"] = 10.0
        self.data["shortwave_radiation_provided"] = False
        self.data["time_step_size_s"] = 3600
        self.data["num_timesteps"] = 720
        self.data["cloud_base_height_known"] = False

        self.data["verbose"] = True
        # TODO: think of how to get user input for fields like this
        self.data["pet_method"] = PetMethod.energy_balance
        # TODO: revisit this. I think this is telling it to use BMI
        self.data["yes_aorc"] = True

        # TODO: FIGURE OUT HOW TO GET THESE PARAMETERS
        # BELOW PARAMETERS MAKE NO SENSE
        self.data["vegetation_height_m"] = 0.12
        self.data["zero_plane_displacement_height_m"] = 0.0003
        self.data["momentum_transfer_roughness_length"] = 0.0
        self.data["heat_transfer_roughness_length_m"] = 0.1
        self.data["surface_longwave_emissivity"] = 42.0
        self.data["surface_shortwave_albedo"] = 7.0

    def build(self) -> BaseModel:
        return PET(**self.data)

    def visit(self, hook_provider: "HookProvider") -> None:
        hook_provider.provide_hydrofabric_linked_data(self)

        if self._version() == "2.0":
            self._v2_defaults()
        else:
            raise RuntimeError("only support v2 hydrofabric")


if __name__ == "__main__":
    hf_file = "/Users/austinraney/Downloads/nextgen_09.gpkg"
    hf_lnk_file = "/Users/austinraney/Downloads/nextgen_09.parquet"

    hf: gpd.GeoDataFrame = gpd.read_file(hf_file, layer="divides")
    hf_lnk_data: pd.DataFrame = pd.read_parquet(hf_lnk_file)

    subset = [
        "cat-1529608",
        "cat-1537245",
        "cat-1529607",
        "cat-1536906",
        "cat-1527290",
    ]

    hf = hf[hf["divide_id"].isin(subset)]
    hf_lnk_data = hf_lnk_data[hf_lnk_data["divide_id"].isin(subset)]

    hook_provider = DefaultHookProvider(hf=hf, hf_lnk_data=hf_lnk_data)

    generate_configs(
        hook_providers=hook_provider,
        hook_objects=[PetHooks],
        file_writer=DefaultFileWriter("./config/"),
    )
