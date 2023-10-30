import random
import time
import polars as pl
from pathlib import Path
import streamlit as st
from tx_client import SyncFHIRTerminologyClient
from tx_client import r4

st.session_state["cm_map"] = []

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
def load_data(bundles:list[Path])->tuple[tuple[r4.Procedure], tuple[r4.Patient]]: 
    """This function loads all the data from bundles on the disk and initializes the closure table."""
    if len(bundles) == 0:
        return tuple(), tuple()
    progress = st.progress(0.0, "Loading...")
    procedures = []
    patients = []
    ### Load all procedure and Patient resources for selected bundles
    for i,bundle_path in enumerate(bundles):
        progress.progress(i/len(bundles), "Loading bundle "+str(i)+" of "+str(len(bundles)))
        bundle = r4.Bundle.parse_file(bundle_path)
        for entry in bundle.entry:
            if entry.resource is not None and entry.resource.resourceType == "Procedure":
                procedures.append(entry.resource)
            if entry.resource is not None and entry.resource.resourceType == "Patient":
                patients.append(entry.resource)
    progress.progress(0.95, "Initializing closure table")

    progress.progress(1.0, "Loading complete")
    return tuple(procedures), tuple(patients)

st.title("Analytics App")

tx_client = SyncFHIRTerminologyClient("http://r4.ontoserver.csiro.au/fhir")

## Selected the patients
patient_bundles = sorted(list(Path("fhir/").glob("*.json")))
form = st.sidebar.form("Select patients")
default_bundles = []
default = form.checkbox("Load default patients")
if default:
    default_bundles = patient_bundles[40:50]

selected_bundles = form.multiselect("Select patients", patient_bundles, format_func=lambda x: x.stem, default=default_bundles)
default_bundles = [bundle for bundle in patient_bundles if "patient" in bundle.stem]
form.form_submit_button("Load")

# This is id is passed to the server to identify the closure table. Make sure it is unique to you.
cm_name = str(random.randint(0,10000))

# Load data and pass the codes of the procedures to the closure api
procedures, patients = load_data(selected_bundles)
sct_codings = set(SCTCoding.parse_obj(coding) for c in procedures if c.code.coding[0].system == "http://snomed.info/sct" for coding in c.code.coding)
tx_client.closure(name=r4.string(cm_name))
cm:r4.ConceptMap = tx_client.closure(name=r4.string(cm_name), concept= list(sct_codings))
st.session_state["cm_map"].extend([c.dict(exclude_none=True) for cm_group in cm.group for c in cm_group.element])

### Convert to polars DataFrames
df_procedures = pl.DataFrame([c.dict(exclude_none=True) for c in procedures])
df_patients = pl.DataFrame([p.dict(exclude_none=True) for p in patients])

### Show the DataFrames
if df_patients.shape[0] > 0:
    with st.expander("Patients preview"):
        st.write(df_patients.select(name=pl.col("name").list.eval(pl.element().struct["family"]+" "+pl.element().struct["given"].list.join(" ")),
                                    identifier=pl.col("identifier").list.eval(pl.element().struct["system"]+"|"+pl.element().struct["value"])
                                    ).head())
    with st.expander("procedures overview"):
        st.table(df_procedures.select(code=pl.col("code").struct["text"]).get_column("code").value_counts())
else:
    st.write("No data loaded yet")

# Pick a SNOMED-CT code to filter on
st.title("Filter on a SNOMED-CT code")
with st.form("my_form"):
   sct_input = st.text_input("Enter a SNOMED-CT code")
   submitted = st.form_submit_button("Submit")
   if submitted:
        pass
       
if not submitted:
    st.stop()

# parse the snomed notation and get the code
sct_coding = SCTCoding.from_sct(sct_input)
st.write("Updating closure table with "+sct_coding.code)
# Update the closure table with the code from the input
cm = tx_client.closure(name=r4.string(cm_name), concept=[r4.Coding.parse_obj({"system":"http://snomed.info/sct", "code":sct_coding.code})])

st.session_state["cm_map"].extend([c.dict(exclude_none=True) for cm_group in cm.group for c in cm_group.element])
### Convert to polars DataFrame

filtered_list = [item for item in st.session_state["cm_map"] if int(item['target'][0]['code']) == int(sct_coding.code)]
df_cm = pl.DataFrame(filtered_list)
if df_cm.shape[0] == 0:
    st.write("No matching concepts found")
    st.stop()
df_cm_flat=df_cm.select(pl.col("target").list.explode().struct["code"].alias("target_code"), pl.col("target").list.explode().struct["equivalence"], source_code=pl.col("code"))
print(df_procedures.columns)
df_procedures_ext = df_procedures\
                        .select(pl.all(), text=pl.col("code").struct["text"],bodysite = pl.col("bodySite"), device= pl.col("focalDevice"),subject_id=pl.col("subject").struct["reference"].str.replace("urn:uuid:", ""))\
                        .join(df_patients, left_on="subject_id", right_on="id")
### Show the DataFrame
with st.expander("Concept Map", expanded=False):
    st.dataframe(df_cm_flat)
    #st.write(df_procedures_ext.get_column("code").struct["coding"].list.explode().struct["code"])


joined_procedures = df_cm_flat\
                .join(df_procedures_ext, left_on="source_code", right_on=pl.col("code").struct["coding"].list.explode().struct["code"])



if joined_procedures.shape[0] > 0:

    st.header("Matching Procedures")
    st.dataframe(joined_procedures
             .select(
                "text",
                "source_code",
                name=pl.col("name").list.first().struct["family"]+" "+pl.col("name").list.first().struct["given"].list.join(" ")
            ).to_pandas())
    
    joined_procedures_groupby = joined_procedures.groupby(by="subject_id").first()
    st.header("Matching Patients")
    st.dataframe(joined_procedures_groupby
             .select(
                "source_code",
                name=pl.col("name").list.first().struct["family"]+" "+pl.col("name").list.first().struct["given"].list.join(" ")
            ).to_pandas())

else:
    st.write("No matching procedures found")


