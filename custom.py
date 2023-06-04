from typing import Literal
from pydantic import Field
import r4

class OperationOutcomeException(RuntimeError):
    def __init__(self, outcome: r4.OperationOutcome):
        self.operation_outcome = outcome
        if outcome.text is not None:
            self.message_html = outcome.text.div
        else:
            self.message_html = self._generate_narrative_html(outcome)
        self.message = self._generate_narrative_text(outcome)
        super().__init__(self.message)
    def _generate_narrative_html(self, outcome: r4.OperationOutcome):
        return "\n".join(f"""<h3>OperationOutcomeException: {issue.severity} {issue.code}</h3><p>{issue.diagnostics}</p>""" for issue in outcome.issue)
    def _generate_narrative_text(self, outcome: r4.OperationOutcome):
        return "\n".join(f"""[OperationOutcomeException] {issue.severity} -- {issue.code}: {issue.diagnostics}""" for issue in outcome.issue)

    def _repr_html_(self):
        return self.message
    
    def __str__(self):
        return self.message



class InvalidFHIRResource(RuntimeError):
    def __init__(self, resource:dict):
        self.resource = resource
        self.message = f"Invalid FHIR resource {resource}"
        super().__init__(self.message)

class Coding(r4.Coding):
    """Extend r4.Coding with from_sct classmethod"""

    def to_search_token(self):
        """Return token for search parameter"""
        return f"{self.system}|{self.code}"

class SCTCoding(Coding):
    
    @classmethod
    def from_sct(cls, token:str):
        """Create SCTCoding from token SNOMED CT inlined code"""
        code, display,_ = token.split('|')
        return cls(system="http://snomed.info/sct", code=code, display=display)

class ExpandedValueSet(r4.ValueSet):

    expansion: r4.ValueSetExpansion

    def _repr_html_(self):
        if self.text is not None:
            return self.text.div
        title = self.title or "No title"
        description = self.description or "No description"
        return f"""
        <h3>{title}</h3>
        <p>{description}</p>
        <table>
        <tr><th>Code</th><th>Display</th></tr>
        {''.join([f'<tr><td>{e.code}</td><td>{e.display}</td></tr>' for e in self.expansion.contains])}
        </table>
        """
ExpandedValueSet.update_forward_refs()

class SearchResultEntry(r4.BundleEntry):
    request: None = None
    response: None = None
    resource: r4.AnyResource

class SearchResult(r4.Bundle):
    type: Literal["searchset"] = Field("searchset", const=True)
    entry: list[SearchResultEntry] = Field(default_factory=list)