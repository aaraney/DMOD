import typing
import io
import abc
import json

import pandas

from .. import specification
from .. import jsonquery

from . import retriever
from . import reader

class FrameRetriever(retriever.CrosswalkRetriever):
    pass


class JSONRetriever(retriever.CrosswalkRetriever):
    @classmethod
    def get_type(cls) -> str:
        return "file"

    @classmethod
    def get_format(cls) -> str:
        return "json"

    def retrieve(self, *args, **kwargs) -> pandas.DataFrame:
        crosswalked_data = reader.select_values(self._document, self.field)
        crosswalked_data.dropna(inplace=True)
        return crosswalked_data

    def __init__(self, definition: specification.CrosswalkSpecification):
        super().__init__(definition)

        full_document: typing.Dict[str, typing.Any] = dict()

        for crosswalk_source in self.backend.sources:
            document = json.loads(self.backend.read(crosswalk_source))
            if not isinstance(document, dict):
                raise ValueError(
                        f"'{crosswalk_source}' is not a valid source for crosswalk data. "
                        f"Only standard JSON data is allowed."
                )
            full_document.update(document)

        self._document = full_document


