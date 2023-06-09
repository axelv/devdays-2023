from __future__ import annotations
from pprint import pprint
from typing import Type, TypedDict, Literal, Unpack
from fhirpy.base import SyncClient, SyncSearchSet, SyncResource
from fhirpy.lib import SyncFHIRResource, SyncFHIRSearchSet, SyncFHIRReference
from .ValueSet import SyncValueSet
from .CodeSystem import SyncCodeSystem
import r4


def convert_dict_to_parameters(data:TypedDict, annotations:dict[str,Type]):
    """Convert a dictionary to a Parameters resource based on the annotations of a TypedDict"""
    return {
            "parameter": [
                {"name": k, "value"+annotations[k].__name__.capitalize(): v} for k,v in data.items()
            ]
        }

class Parameter(r4.ParametersParameter):
    @property
    def value_(self):
        for field in self.__fields__.keys(): # type: ignore
            if field.startswith("value") and getattr(self, field, None) is not None:
                return getattr(self, field)
        return None

class ClosureKwargs(TypedDict, total=False):
    name: r4.string
    concept: list[r4.Coding]
    version: r4.string

class ClosureParametersIn(r4.Parameters):
    resourceType: Literal["Parameters"] = "Parameters"
    parameter: list[Parameter]

    @classmethod
    def from_kwargs(cls, name: r4.string, concept: list[r4.Coding] = [], version: r4.string|None = None, **kwargs):
        parameters = {
            "parameter": [
                *({"name": "concept", "valueCoding": concept} for concept in concept),
                {"name": "name", "valueString": name},
            ]
        }
        parsed =  cls.parse_obj(parameters)
        return parsed


class SyncFHIRTerminologyClient(SyncClient):

    CURRENT_CLIENT:list[SyncFHIRTerminologyClient] = []

    ALLOWED_TYPES = {"ValueSet", "CodeSystem"}
    searchset_class:Type[SyncSearchSet] = SyncFHIRSearchSet
    resource_class:Type[SyncResource] = SyncFHIRResource

    def reference(self, resource_type=None, id=None, reference=None, **kwargs):
        if resource_type and id:
            reference = "{0}/{1}".format(resource_type, id)

        if not reference:
            raise TypeError(
                "Arguments `resource_type` and `id` or `reference` " "are required"
            )
        return SyncFHIRReference(self, reference=reference, **kwargs)

    def resource(self, resource_type=None, **kwargs):
        if resource_type not in self.ALLOWED_TYPES:
            raise TypeError(
                "Resource type `{}` is not allowed. Allowed types: {}".format(
                    resource_type, ", ".join(self.ALLOWED_TYPES)
                )
            )
        if resource_type == "ValueSet":
            return SyncValueSet(self, **kwargs)

        if resource_type == "CodeSystem":
            return SyncCodeSystem(self, **kwargs)

        return super().resource(resource_type, **kwargs)
    
    def ValueSet(self, **kwargs):
        return SyncValueSet(self, **kwargs)

    def CodeSystem(self, **kwargs):
        return SyncCodeSystem(self, **kwargs)

    def closure(self, **kwargs:Unpack[ClosureKwargs]):
        """Closure operation"""
        data = ClosureParametersIn.from_kwargs(**kwargs).dict(exclude_none=True)
        pprint(data)
        result = self.execute("$closure", method="POST", data=data)
        return r4.ConceptMap.parse_obj(result)

    def __enter__(self):
        self.CURRENT_CLIENT.append(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.CURRENT_CLIENT.pop()