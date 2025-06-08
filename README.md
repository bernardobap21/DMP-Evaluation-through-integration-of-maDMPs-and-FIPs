# DMP-Evaluation

This repository contains a prototype framework for evaluating machine-actionable Data Management Plans (maDMPs) using a FAIR Implementation Profile (FIP). It provides a command line tool and a small API for running the evaluation.

## Prerequisites

* Python 3.8 or newer
* Recommended: create and activate a virtual environment

## Installation

Install the required packages with:

```bash
pip install -r requirements.txt
```

## Running the evaluator

The main script `evaluate_dmp.py` compares a maDMP file with the FIP mapping and generates several reports. A minimal example can be executed with:

```bash
python evaluate_dmp.py \
  --input examples/dmp_minimal.json \
  --mapping FIP_Mapping/fip_madmp_mapping.json \
  --output results
```

This will produce:

* `*_evaluation.csv` – table of FIP questions, mapping status and whether each field is present in the maDMP
* `*_recommendations.txt` – short textual recommendations for missing fields
* `*_fairness.json` – completeness, accuracy and other FAIRness scores
* `*_metadata_validation.json` – validation of metadata against basic rules
* `*_planned_fairness.json` – evaluation of the planned FAIRness of distributions

## Starting the API

An HTTP API exposing the same evaluation logic is provided in `api.py`. Start it with:

```bash
uvicorn api:app --reload
```

The API will be available at `http://127.0.0.1:8000/`.

## FAIR Implementation Profile mapping

The file `FIP_Mapping/fip_madmp_mapping.json` defines how each FIP question relates to fields in a maDMP. Each entry lists the FAIR principle, the original question, the corresponding maDMP path and the mapping status (e.g. `Mapped`, `Partially Mapped`). During evaluation the mapping guides the checks that populate the reports listed above.

