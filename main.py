#%%
from requests import get
from pydantic import ValidationError 
import r4
from custom import ExpandedValueSet, SCTCoding, SearchResult, OperationOutcomeException, InvalidFHIRResource

TX_SERVER = 'https://r4.ontoserver.csiro.au/fhir'
FHIR_SERVER = 'https://server.fire.ly/r4'

def expand_valueset(query:str, *, url: str, count: int = 10):
    """Get ValueSet expansion from FHIR server"""
    url = f'{TX_SERVER}/ValueSet/$expand?url={url}&filter={query}&count={count}'
    response = get(url)
    return ExpandedValueSet.parse_raw(response.text)

def get_conditions_by_sct_code(sct_code, *, count:int|None = None):
    """Get all carcinoma conditions from FHIR server"""
    code = SCTCoding.from_sct(sct_code)
    url = f'{FHIR_SERVER}/Condition?code:below={code.to_search_token()}&_count={count}'
    response = get(url)
    try:
        search_result = SearchResult.parse_obj(response.json())
        for entry in search_result.entry:
            if entry.resource.resourceType == "Condition":
                yield entry.resource
            elif entry.resource.resourceType == "OperationOutcome":
                raise OperationOutcomeException(entry.resource)
            else:
                raise ValueError(f"Unexpected resource type {entry.resource.resourceType}")
    except ValidationError:
        pass
    try:
        operation_outcome = r4.OperationOutcome.parse_obj(response.json())
        raise OperationOutcomeException(operation_outcome) 
    except ValidationError:
        raise InvalidFHIRResource(response.json()) from e

def snomed_ct_lookup(code:str, *, url: str):
    """Get ValueSet expansion from FHIR server"""
    url = f'{TX_SERVER}/CodeSystem/$expand?url=http://snomed.info&code={code}'
    response = get(url)
    return r4.Parameters.parse_raw(response.text)

#%%
try:
    for condition in get_conditions_by_sct_code("363346000 |kanker|", count=10):
        print(condition.code)
except OperationOutcomeException as e:
    print(e.message)


# %%
