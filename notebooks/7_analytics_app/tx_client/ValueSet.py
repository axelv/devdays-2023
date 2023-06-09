from typing import TypedDict, Unpack, Iterator, Type, Annotated, cast, Literal
from fhirpy.lib import SyncFHIRResource
from . import r4

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

class ExpandedValueSet(r4.ValueSet):
    expansion: r4.ValueSetExpansion

class ValidateCodeKwargs(TypedDict, total=False):
    url: r4.uri
    context: r4.uri
    valueSet: r4.ValueSet
    valueSetVersion: r4.string
    code: r4.code
    system: r4.string
    systemVersion: r4.uri
    display: r4.string
    coding: r4.Coding
    codeableConcept: r4.CodeableConcept
    date: r4.dateTime
    abstract: r4.boolean
    displayLanguage: r4.code
    useSupplement: list[r4.canonical]

class ValidateCodeParametersIn(r4.Parameters):
    resourceType: Literal["Parameters"] = "Parameters"
    parameter: list[Parameter]

    @classmethod
    def from_kwargs(cls, kwargs:ValidateCodeKwargs):
        return cls.parse_obj(convert_dict_to_parameters(kwargs, ValidateCodeKwargs.__annotations__))
   
class ValidateCodeResult(TypedDict):
    result: r4.boolean
    message: r4.string
    display: r4.string
    code: r4.code
    system: r4.uri
    version: r4.string
    codeableConcept: r4.CodeableConcept
    issues: r4.OperationOutcome

class ValidateCodeParametersOut(r4.Parameters):
    resourceType: Literal["Parameters"] = "Parameters"
    parameter: list[Parameter]

    def to_dict(self) -> ValidateCodeResult:
        return cast(ValidateCodeResult,{p.name: p.value_ for p in self.parameter})


class ExpandKwargs(TypedDict, total=False):
    url: r4.uri
    valueSet: r4.ValueSet
    valueSetVersion: r4.string
    context: r4.uri
    contextDirection: r4.code
    filter: r4.string
    date: r4.dateTime
    offset: r4.integer
    count: r4.integer
    includeDesignations: r4.boolean
    designation: list[r4.string]
    includeDefinition: r4.boolean
    activeOnly: r4.boolean
    excludeNested: r4.boolean
    excludeNotForUI: r4.boolean
    useSupplement: list[r4.canonical]
  
class ExpandParametersIn(r4.Parameters):
    resourceType: Literal["Parameters"] = "Parameters"
    parameter: list[Parameter]

    @classmethod
    def from_kwargs(cls, kwargs:ExpandKwargs):
        return cls.parse_obj(convert_dict_to_parameters(kwargs, ExpandKwargs.__annotations__)) 


class SyncValueSet(SyncFHIRResource):
    def __init__(self, client, **kwargs):
        super().__init__(client, "ValueSet", **kwargs)

    def expand(self,**kwargs: Unpack[ExpandKwargs]):
        """Expand a ValueSet resource and return a ValueSet resource with the expanded ValueSet.
        https://www.hl7.org/fhir/valueset-operation-expand.html"""
        data = ExpandParametersIn.from_kwargs(kwargs).dict(exclude_none=True)
        result = self.execute(
            "$expand",
            method="POST",
            data=data
        )
        return ExpandedValueSet.parse_obj(result)


    def validate_code(self, **kwargs:Unpack[ValidateCodeKwargs]):
        """Validate a code against a ValueSet resource.
        https://www.hl7.org/fhir/valueset-operation-validate-code.html"""
        result = self.execute(
            "$validate-code",
            method="POST",
            data=ValidateCodeParametersIn.from_kwargs(kwargs).dict(exclude_none=True)
        )
        return ValidateCodeParametersOut.parse_obj(result).to_dict()
    
    def __iter__(self) -> Iterator[r4.Coding]:
        vs:r4.ValueSet = self.expand()
        if vs.expansion is None:
            raise ValueError("ValueSet expansion is empty")
        contains:list[r4.ValueSetExpansionContains] = vs.expansion.contains
        yield from self.__iterate_codings(contains)
    
    def __iterate_codings(self, contains:list[r4.ValueSetExpansionContains]):
        for coding in contains:
            yield r4.Coding(code=coding.code, system=coding.system, display=coding.display)
            if coding.contains:
                yield from self.__iterate_codings(coding.contains)
    
    def __contains__(self, __o: object) -> bool:
        
        if isinstance(__o, r4.Coding):
            response = self.validate_code(coding=__o)
            return response['result']

        if isinstance(__o, r4.CodeableConcept):
            response = self.validate_code(codeableConcept=__o)
            return response['result']

        raise NotImplementedError("Can only check for Coding objects.")