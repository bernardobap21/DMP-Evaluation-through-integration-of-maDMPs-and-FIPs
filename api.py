from fastapi import FastAPI, UploadFile, File, Query, Body
import json
from Evaluator.evaluator import (
    load_dmp,
    evaluate_dmp_against_fip,
)
from Evaluator.ostrails_formatter import export_fip_results, DEFAULT_VERSION
from FIP_Mapping.mapping import load_mapping
from FIP_Mapping.utils import transform_mapping
from scripts.nanopub_to_mapping import build_mapping, get_fip_label
import tempfile
import os


FIP_DIRECTORY = "FIP_Mapping"


def get_fip_options():
    """Return a list of available FIP mapping JSON files."""
    return [f for f in os.listdir(FIP_DIRECTORY) if f.endswith(".json")]


# List used for Query enum. Updated when new mappings are uploaded.
FIP_OPTIONS = get_fip_options()
fip_query = Query(..., enum=FIP_OPTIONS)

def convert_nanopub_to_mapping(url: str) -> str:
    """Fetch a nanopublication and store the generated mapping."""
    mapping = build_mapping(url)
    label = get_fip_label(url)
    os.makedirs(FIP_DIRECTORY, exist_ok=True)
    filename = f"fip_madmp_{label}.json"
    path = os.path.join(FIP_DIRECTORY, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2)
    return filename

def build_compliance_json(results):
    table = []
    for r in results:
        allowed_values = r["allowed_values"]
        if isinstance(allowed_values, list):
            allowed_str = ", ".join(allowed_values)
        else:
            allowed_str = allowed_values

        comp = r.get("compliance_list") or r.get("compliance_status")
        if allowed_values == "":
            compliant = "No choice made by community"
        else:
            if isinstance(comp, list):
                entries = ["Yes" if c == "Compliant" else "No" for c in comp]
                compliant = f"[{', '.join(entries)}]"
            else:
                compliant = "Yes" if comp == "Compliant" else "No"

        table.append({
            "FIP Question": r["FIP_question"],
            "DCS Field": r["DCS_field"],
            "maDMP Value": r["field_value"],
            "Accepted Values": allowed_str,
            "Compliant": compliant,  
        })
    return table


app = FastAPI()


@app.get("/")
def read_root():
    return {"Welcome": "Your DMP Evaluation API is running!"}


@app.post("/upload_fip/")
async def upload_fip(
    uri: str = Body(
        ...,
        embed=False,
        title="Insert nanopublication link",
        description="Nanopublication URL",
        example="Paste the nanopublication URL here between quotes", 
    ),
):
    """Fetch a FIP nanopublication and store it as a mapping JSON."""
    mapping = build_mapping(uri)
    label = get_fip_label(uri)
    filename = f"fip_madmp_{label}.json"
    dest_path = os.path.join(FIP_DIRECTORY, filename)
    with open(dest_path, "w", encoding="utf-8") as out_file:
        json.dump(mapping, out_file, indent=2)

    # Recalculate options so the evaluate endpoint dropdown updates
    global FIP_OPTIONS, fip_query
    FIP_OPTIONS[:] = get_fip_options()
    fip_query.enum = FIP_OPTIONS
    app.openapi_schema = None

    return {"filename": filename, "detail": "Uploaded"}


@app.post("/evaluate/")
async def evaluate(
    maDMP_file: UploadFile = File(...),
    fip_mapping_file: str = fip_query,
):

    # Validate uploaded DMP file
    if not maDMP_file.filename.endswith(".json"):
        return {
            "error": f"Invalid file type: {maDMP_file.filename}. Only .json files are allowed."
        }
    
    options = get_fip_options()
    if fip_mapping_file not in options:
        return {
            "error": f"Mapping file '{fip_mapping_file}' not found.",
            "available": options,
        }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        dmp_path = os.path.join(tmpdir, maDMP_file.filename)

        with open(dmp_path, "wb") as buffer:
            buffer.write(await maDMP_file.read())

        mapping_path = os.path.join(FIP_DIRECTORY, fip_mapping_file)

        # Load DMP and mapping
        dmp = load_dmp(dmp_path)
        mapping_raw = load_mapping(mapping_path)
        mapping = transform_mapping(mapping_raw)

        # Evaluate
        results = evaluate_dmp_against_fip(dmp, mapping)
        

        # Build OSTrails results
        base_filename = os.path.splitext(maDMP_file.filename)[0]
        fip_version = mapping_raw.get("FIP_Version", DEFAULT_VERSION)
        ftr_ready = []
        for idx, r in enumerate(results, start=1):
            metric_id = f"FIP{str(idx).zfill(2)}.Q{idx}"
            benchmark = r.get("allowed_values", [])
            if benchmark and not isinstance(benchmark, list):
                benchmark = [benchmark]

            fair_principle = r.get("FAIR_principle")
            field_val = json.dumps(r.get("field_value"), ensure_ascii=False)
            comment = (
                f"Field status: {r['field_status']}; maDMP value: {field_val}; compliance: {r['compliance_status']}"
            )

            values = r.get("field_value")
            if not isinstance(values, list):
                values = [values]

            comp_list = r.get("compliance_list") or r.get("compliance_status")
            if not isinstance(comp_list, list):
                comp_list = [comp_list]

            log_val = []
            status_vals = []
            for val, comp in zip(values, comp_list):
                if isinstance(val, (dict, list)):
                    log_val.append(json.dumps(val, ensure_ascii=False))
                else:
                    log_val.append(str(val))
                if not r.get("allowed_values"):
                    status_vals.append("indeterminate")
                else:
                    status_vals.append(
                        "pass" if r["field_status"] == "Present" and comp == "Compliant" else "fail"
                    )

            ftr_ready.append(
                {
                    "metric_id": metric_id,
                    "metric_label": r["FIP_question"],
                    "test_id": f"Test_{metric_id}",
                    "benchmark": benchmark,
                    "fair_principle": fair_principle,
                    "comment": comment,
                    "log_value": log_val,
                    "subject": r["DCS_field"],
                    "status": status_vals,
                }
            )

        jsonld_path = export_fip_results(
            ftr_ready,
            dmp_id=base_filename,
            dmp_title=dmp.get("title", base_filename),
            output_dir=tmpdir,
            metric_version=fip_version,
        )

        with open(jsonld_path, "r", encoding="utf-8") as fh:
            ostrails_jsonld = json.load(fh)

        compliance_table = build_compliance_json(results)

    return {
        "Mapping used": mapping_raw,
        "OSTrails compliant result": ostrails_jsonld,
        "Compliance table": compliance_table,
    }


