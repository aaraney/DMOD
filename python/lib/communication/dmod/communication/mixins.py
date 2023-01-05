from pydantic.fields import ModelField
from pprint import pformat
from typing import Any, Dict, Union

# TEMP: import from dmod.core
class EnumValidateByNameMixIn:
    @classmethod
    def __modify_schema__(cls, field_schema: Dict[str, Any], field: ModelField) -> None:
        # display enum field names as field options
        if "enum" in field_schema:
            field_schema["enum"] = [f.name.upper() for f in field.type_]
            field_schema["type"] = "string"

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Union['EnumValidateByNameMixIn', str]):
        if isinstance(v, cls):
            return v

        v = str(v).upper()

        for name, value in cls.__members__.items():
            if name.upper() == v:
                return value

        error_message = pformat(
            f"Invalid Enum field. Field {v!r} is not a member of {set(cls.__members__)}"
        )
        raise ValueError(error_message)

    def __repr__(self) -> str:
        return self.name
