from typing import TYPE_CHECKING, Sequence, Tuple, Optional, Any, Union, AbstractSet, Mapping
import json
from pydantic import BaseModel as PydanticBaseModel

if TYPE_CHECKING:
    ReprArgs = Sequence[Tuple[Optional[str], Any]]
    AbstractSetIntStr = AbstractSet[Union[int, str]]
    MappingIntStrAny = Mapping[Union[int, str], Any]

def _is_empty(value: Any) -> bool:
    try:
        return len(value) == 0
    except TypeError:
        return value is None

class FHIREncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, dict):
            return_obj = dict()
            for k, v in obj.items():
                if v is None:
                    continue
                try:
                    if len(v) == 0:
                        continue
                except TypeError:
                    pass
                return_obj[k] = v
        else:
            return_obj = super().default(obj)
        return return_obj

def json_dumps(v, *, default):
    return json.dumps(v, default=default, indent=2, cls=FHIREncoder)


class BaseModel(PydanticBaseModel):
    def __repr_args__(self) -> 'ReprArgs':
        return [
            (k, v)
            for k, v in super().__repr_args__() if (k not in self.__fields__ or self.__fields__[k].field_info.extra.get("summary", True)) and not _is_empty(v)
        ]
    def _repr_html_(self):
        if "text" in self.__fields__ and self.text is not None: # type: ignore
            return self.text.div # type: ignore

    class Config:
        json_dumps = json_dumps