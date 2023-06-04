import logging
logging.basicConfig(level=logging.INFO)
import json
from pathlib import Path
from pydantic import ValidationError
import r4


LOGGER = logging.getLogger(__name__)
def to_bundle(path: Path) -> r4.Bundle:
    """Convert a folder of StructureDefinitions to a Bundle"""
    bundle = r4.Bundle(resourceType="Bundle", type="collection")
    for sd_path in path.glob("StructureDefinition*.json"):
        LOGGER.info(f"Adding {sd_path.stem} to bundle")
        try:
            sd = r4.StructureDefinition.parse_file(str(sd_path))
        except ValidationError as e:
            LOGGER.error(f"Error parsing {sd_path}: {e}")
            continue
        bundle.entry.append(r4.BundleEntry(resource=sd))
    return bundle

if __name__ == "__main__":
    import sys
    bundle = to_bundle(Path(sys.argv[1]))
    dest_path = Path(sys.argv[2])
    with open(dest_path / "fhir.mcode-profiles.json", "w") as f:
        f.write(bundle.json(exclude_none=True))

    

