from __future__ import annotations
from typing import Type
from fhirpy.base import SyncClient, SyncSearchSet, SyncResource
from fhirpy.lib import SyncFHIRResource, SyncFHIRSearchSet, SyncFHIRReference, SyncReference
from .ValueSet import SyncValueSet
from .CodeSystem import SyncCodeSystem


class SyncFHIRTerminologyClient(SyncClient):

    CURRENT_CLIENT:list[SyncFHIRTerminologyClient] = []

    ALLOWED_TYPES = {"ValueSet", "CodeSystem", "ConceptMap"}
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

    def __enter__(self):
        self.CURRENT_CLIENT.append(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.CURRENT_CLIENT.pop()