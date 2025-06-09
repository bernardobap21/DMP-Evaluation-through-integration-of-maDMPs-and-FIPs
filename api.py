from fastapi import FastAPI, UploadFile, File
from Evaluator.evaluator import (
    load_dmp,
    evaluate_dmp_against_fip,
    summarize_results,
)
from Evaluator.fairness_checks import run_fairness_scoring
from Evaluator.validation_rules import validate_metadata_intentions
#from Evaluator.planned_fairness import check_planned_fairness
from FIP_Mapping.mapping import load_mapping
from FIP_Mapping.utils import transform_mapping
import tempfile
import os

app = FastAPI()


@app.get("/")
def read_root():
    return {"Welcome": "Your DMP Evaluation API is running!"}


@app.post("/evaluate/")
async def evaluate(dmp_file: UploadFile = File(...), fip_mapping_file: UploadFile = File(...)):

    for uploaded_file in [dmp_file, fip_mapping_file]:
        if not uploaded_file.filename.endswith(".json"):
            return {
                "error": f"Invalid file type: {uploaded_file.filename}. Only .json files are allowed."
            }
        
    # Temporarily save uploaded files
    with tempfile.TemporaryDirectory() as tmpdir:
        dmp_path = os.path.join(tmpdir, dmp_file.filename)
        mapping_path = os.path.join(tmpdir, fip_mapping_file.filename)

        with open(dmp_path, "wb") as buffer:
            buffer.write(await dmp_file.read())

        with open(mapping_path, "wb") as buffer:
            buffer.write(await fip_mapping_file.read())

        # Load DMP and mapping
        dmp = load_dmp(dmp_path)
        mapping_raw = load_mapping(mapping_path)
        mapping = transform_mapping(mapping_raw)

        # Evaluate
        results = evaluate_dmp_against_fip(dmp, mapping)
        present, total = summarize_results(results)

        # Additional checks
        fairness_results = run_fairness_scoring(dmp)
        metadata_validation = validate_metadata_intentions(dmp)
        #planned_fairness = check_planned_fairness(dmp)

    # Return results as JSON
    return {
        "summary": f"{present}/{total} fields present\n",
        "fairness": fairness_results,
        "metadata_validation": metadata_validation,
        "Mapping_to_FIP_Results": results,
        #"planned_fairness": planned_fairness,
    }
