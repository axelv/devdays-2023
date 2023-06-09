from fhirpy.lib import SyncFHIRResource

class SyncCodeSystem(SyncFHIRResource):
    def __init__(self, client, **kwargs):
        super().__init__(client, "CodeSystem", **kwargs)