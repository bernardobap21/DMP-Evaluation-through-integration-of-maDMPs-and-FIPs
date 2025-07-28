# DMP-Evaluation

This repository contains a prototype framework for evaluating Data Management Plans (DMPs) by integrating machine-actionable Data Management Plans (maDMPs) and FAIR Implementation Profiles (FIPs). It provides a command line tool and a small API for running the evaluation.

## Prerequisites

* Python 3.8 or newer

## Installation

First clone the repository and move into the project directory:

```bash
git clone https://github.com/bernardobap21/DMP-Evaluation.git
cd DMP-Evaluation
```

Then install the required packages with:

```bash
pip install -r requirements.txt
```

## Running the evaluator

After installing the dependencies you can run the evaluator. The script `evaluate_dmp.py` compares a maDMP file with a chosen FIP mapping and generates several reports. An example using the included files is:

```bash
python  evaluate_dmp.py --input examples/Plant-flower_visitor_interactions.json --mapping FIP_Mapping/fip_madmp_Plant-Pollinator Community.json --output results
```

This will produce:

* `*_compliance_table.csv` – table of FIP questions, to which maDMP they are mapped to (in case it is true), the given value for this field, what is the accepted/allowed values and whether each field is compliant to the FIP used for the evaluation or not.
* `*_recommendations.txt` – short textual recommendations for missing fields
* `*_goals_checks.json` – Scores for the following goals: Completeness, Accuracy, Availability and Consistency.
* `*_metadata_validation.json` – validation of metadata against basic rules
* `*_ostrails_results.jsonld` – evaluation of the maDMP following the OSTrails FAIR Test Results vocabulary.

## Starting the API

An HTTP API exposing the same evaluation logic is provided in `api.py`. Start it with:

```bash
python -m uvicorn api:app --reload
```
The server will run on `http://127.0.0.1:8000`. Open `http://127.0.0.1:8000/docs` in your browser to access the interactive documentation. You can upload your maDMP file and pick a FIP mapping from the dropdown to run an evaluation directly from the web UI.

The API is also available on the web at  `https://dmp-evaluation.onrender.com/docs#/default/evaluate_evaluate__post`.

Click the Try it out button and then, upload your maDMP file and select one of the available FIPs for the evaluation from the dropdown or add a new FIP mapping by using the upload FIP tool. Just paste the linkt to the nanopublication between the quotes ("") and the mapping will be added to the dropdown of the evaluation tool. 

This will return in the `Response body`:

*  – The FIP mapping used to evaluate the maDMP. 
*  – The evaluation in a OSTrails compliant format (JSON-LD).
*  – The compliance table showing the values present in the maDMP and the allowed values from the FIP used for the evaluation.

## FAIR Implementation Profile mapping

The files `FIP_Mapping/fip_madmp_*.json` define how each FIP question relates to fields in a maDMP (following the structure of the RDA DMP Common Standard for machine-actionable Data Management Plans) . Each entry lists the FAIR principle, the original question, the corresponding maDMP path and the mapping status (`Mapped`, `Partially Mapped`, `Not Mapped`). During evaluation the mapping guides the checks that populate the reports listed above.

## Examples and results

Several sample maDMPs are provided in the `examples/` directory. Running the evaluator with these files will produce the outputs listed above in the folder passed via `--output`. Pre-generated reports can be found in `results/`.

## Additional tools

The `scripts/` directory contains helper utilities:

* `json_to_rdf.py` – convert a maDMP JSON file to a Turtle representation.

The `Evaluator/` module includes Goals evaluation scoring (`goals_checks.py`) and metadata validation (`validation_rules.py`).

Mappings for different communities are stored under `FIP_Mapping/`.