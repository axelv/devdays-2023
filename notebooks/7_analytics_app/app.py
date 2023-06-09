import polars as pl
from pathlib import Path
import streamlit as st
from tx_client import SyncFHIRTerminologyClient
from tx_client import r4

st.session_state["cm_map"] = []
st.session_state["version"] = 0

class SCTCoding(r4.Coding):

    def __hash__(self):
        return hash((self.system, self.code))

    @classmethod
    def from_sct(cls,token:str):
        parts = token.split("|")
        if len(parts) == 2:
            code, display = parts
        else:
            code,display = parts[0],None
        return cls(system="http://snomed.info", code=code, display=display)

@st.cache_data
def load_data(bundles:list[Path])->tuple[tuple[r4.Condition], tuple[r4.Patient]]: 
    """This function loads all the data from bundles on the disk and initializes the closure table."""
    if len(bundles) == 0:
        return tuple(), tuple()
    progress = st.progress(0.0, "Loading...")
    conditions = []
    patients = []
    ### Load all Condition and Patient resources for selected bundles
    for i,bundle_path in enumerate(bundles):
        progress.progress(i/len(bundles))
        bundle = r4.Bundle.parse_file(bundle_path)
        for entry in bundle.entry:
            if entry.resource is not None and entry.resource.resourceType == "Condition":
                conditions.append(entry.resource)
            if entry.resource is not None and entry.resource.resourceType == "Patient":
                patients.append(entry.resource)
    progress.progress(0.95, "Initializing closure table")

    progress.progress(1.0, "Loading complete")
    return tuple(conditions), tuple(patients)

@st.cache_resource
def init_cm(_codes:list[r4.Coding], name, version):
    tx_client.closure(name=r4.string(name))
    cm:r4.ConceptMap = tx_client.closure(name=r4.string(name), concept=_codes, version=version)
    st.session_state["cm_map"].extend([c.dict(exclude_none=True) for cm_group in cm.group for c in cm_group.element])
    st.session_state["version"] = cm.version

st.title("Analytics App")

tx_client = SyncFHIRTerminologyClient("http://r4.ontoserver.csiro.au/fhir")

## Selected the patients
patient_bundles = list(Path("fhir/").glob("*.json"))
form = st.sidebar.form("Select patients")
selected_bundles = form.multiselect("Select patients", patient_bundles, format_func=lambda x: x.stem)
form.form_submit_button("Load")

# This is id is passed to the server to identify the closure table. Make sure it is unique to you.
cm_name = st.sidebar.text_input("Session id", key="session_id", value="your-unique-test-id")

# Load data and pass the codes of the conditions to the closure api
conditions, patients = load_data(selected_bundles)
sct_codings = set(SCTCoding.parse_obj(coding) for c in conditions if c.code.coding[0].system == "http://snomed.info/sct" for coding in c.code.coding)
init_cm(_codes=list(sct_codings), name=cm_name, version=st.session_state["version"])

### Convert to polars DataFrames
df_conditions = pl.DataFrame([c.dict(exclude_none=True) for c in conditions])
df_patients = pl.DataFrame([p.dict(exclude_none=True) for p in patients])

### Show the DataFrames
if df_patients.shape[0] > 0:
    with st.expander("Patients preview"):
        st.write(df_patients.select(name=pl.col("name").list.eval(pl.element().struct["family"]+" "+pl.element().struct["given"].list.join(" ")),
                                    identifier=pl.col("identifier").list.eval(pl.element().struct["system"]+"|"+pl.element().struct["value"])
                                    ).head())
    with st.expander("Conditions overview"):
        st.table(df_conditions.select(code=pl.col("code").struct["text"]).get_column("code").value_counts())
else:
    st.write("No data loaded yet")

# Pick a SNOMED-CT code to filter on
st.title("Filter on a SNOMED-CT code")
sct_input = st.text_input("Enter a SNOMED-CT code")
if not sct_input:
    st.stop()

# parse the snomed notation and get the code
sct_coding = SCTCoding.from_sct(sct_input)
st.write("Updating closure table with "+sct_coding.code)
# Update the closure table with the code from the input
cm = tx_client.closure(name=r4.string(cm_name), concept=[r4.Coding.parse_obj({"system":"http://snomed.info/sct", "code":sct_coding.code})])

st.session_state["cm_map"].extend([c.dict(exclude_none=True) for cm_group in cm.group for c in cm_group.element])
### Convert to polars DataFrame
df_cm = pl.DataFrame(st.session_state["cm_map"])
if df_cm.shape[0] == 0:
    st.write("No matching concepts found")
    st.stop()
df_cm_flat=df_cm.select(pl.col("target").list.explode().struct["code"].alias("target_code"), pl.col("target").list.explode().struct["equivalence"], source_code=pl.col("code"))
df_conditions_ext = df_conditions\
                        .select(pl.all(), text=pl.col("code").struct["text"], subject_id=pl.col("subject").struct["reference"].str.replace("urn:uuid:", ""))\
                        .join(df_patients, left_on="subject_id", right_on="id")

### Show the DataFrame
with st.expander("Concept Map", expanded=False):
    st.write(df_cm_flat)
    st.write(df_conditions_ext.get_column("code").struct["coding"].list.explode().struct["code"])


joined_conditions = df_cm_flat\
                .join(df_conditions_ext, left_on="source_code", right_on=pl.col("code").struct["coding"].list.explode().struct["code"])\
                .groupby(by="subject_id")\
                .first()
if joined_conditions.shape[0] > 0:
    st.dataframe(joined_conditions
             .select(
                "subject_id",
                "text",
                "birthDate",
                name=pl.col("name").list.first().struct["family"]+" "+pl.col("name").list.first().struct["given"].list.join(" ")
            ).to_pandas())
else:
    st.write("No matching conditions found")


