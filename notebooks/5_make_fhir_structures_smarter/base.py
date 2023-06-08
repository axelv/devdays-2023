import re
from typing import TYPE_CHECKING, Callable, Sequence, Tuple, Optional, Any, Union, AbstractSet, Mapping
from pydantic import BaseModel as PydanticBaseModel
from pydantic.utils import sequence_like

if TYPE_CHECKING:
    ReprArgs = Sequence[Tuple[Optional[str], Any]]
    AbstractSetIntStr = AbstractSet[Union[int, str]]
    MappingIntStrAny = Mapping[Union[int, str], Any]

class BaseModel(PydanticBaseModel):

    def _repr_html_(self):
        if "text" in self.__fields__ and self.text is not None: # type: ignore
            return self.text.div # type: ignore

    def __repr_args__(self) -> "ReprArgs":
        return [(k,v) for k,v in super().__repr_args__() if v is not None and (not sequence_like(v) or len(v) > 0)] # type: ignore

    def json(self, *, include: Union["AbstractSetIntStr", "MappingIntStrAny"]|None = None, exclude: Union["AbstractSetIntStr" , "MappingIntStrAny"] | None = None, by_alias: bool = False, skip_defaults: bool | None = None, exclude_unset: bool = False, exclude_defaults: bool = False, exclude_none: bool = True, encoder: Callable[[Any], Any] | None = None, models_as_dict: bool = True, **dumps_kwargs: Any) -> str:
        return super(BaseModel,self).json(include=include, exclude=exclude, by_alias=by_alias, skip_defaults=skip_defaults, exclude_unset=exclude_unset, exclude_defaults=exclude_defaults, exclude_none=exclude_none, encoder=encoder, models_as_dict=models_as_dict, **dumps_kwargs)


class Date(str):

    def __new__(cls, value:str,* , year:int|None, month:int|None, day:int|None, **kwargs):
        # explicitly only pass value to the str constructor
        return super(Date, cls).__new__(cls, value)
    
    def __init__(self, value:str, *, year:int|None, month:int|None, day:int|None, **kwargs) -> None:
        self.year = year
        self.month = month
        self.day = day

    PARTIAL_DATE_REGEX = re.compile(r'^([0-9]{4})(?:-([0-9]{2})(?:-([0-9]{2}))?)?$')

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise TypeError('string required')
        m = cls.PARTIAL_DATE_REGEX.fullmatch(v.upper())
        if not m:
            raise ValueError('invalid date format')
        year = int(m.group(1)) if m.group(1) else None
        month = int(m.group(2)) if m.group(2) else None
        day = int(m.group(3)) if m.group(3) else None
        return cls(f"{m.group(1)}-{m.group(2)}-{m.group(3)}", year=year, month=month, day=day)

    def __repr__(self):
        return f"Date(year={self.year}, month={self.month}, day={self.day})"
    
    def __str__(self):
        return "-".join([str(t) for t in (self.year, self.month, self.day) if t is not None])
