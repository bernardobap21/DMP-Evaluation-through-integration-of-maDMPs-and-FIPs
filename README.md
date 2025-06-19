# DMP-Evaluation

This repository contains a prototype framework for evaluating Data Management Plans (DMPs) by integrating machine-actionable Data Management Plans (maDMPs) and FAIR Implementation Profiles (FIPs). It provides a command line tool and a small API for running the evaluation.

## Prerequisites

* Python 3.8 or newer

## Installation

Install the required packages with:

```bash
pip install -r requirements.txt
```

## Running the evaluator

The main script `evaluate_dmp.py` compares a maDMP file with the FIP mapping and generates several reports. An example with a maDMP and a FIP (both available in the repository) of how it can be executed is:

```bash
python evaluate_dmp.py --input examples/ex9-dmp-long.json --mapping FIP_Mapping/fip_madmp_mapping.json --output results
```

This will produce:

* `*_evaluation.csv` – table of FIP questions, mapping status and whether each field is present in the maDMP
* `*_recommendations.txt` – short textual recommendations for missing fields
* `*_fairness.json` – Scores for the following goals: completeness, accuracy, consistency and guidance_compliance (this will be extended in the future)
* `*_metadata_validation.json` – validation of metadata against basic rules
* `*_planned_fairness.json` – evaluation of the planned FAIRness of distributions (early stages of a DMP)

## Starting the API

An HTTP API exposing the same evaluation logic is provided in `api.py`. Start it with:

```bash
python -m uvicorn api:app --reload
```

The API is available locally at `http://127.0.0.1:8000/docs`.

Or in the web at  `https://dmp-evaluation.onrender.com/docs`.

When using the interactive documentation, upload your maDMP file and select one of the available mapping files from the dropdown.

## FAIR Implementation Profile mapping

The file `FIP_Mapping/fip_madmp_mapping.json` defines how each FIP question relates to fields in a maDMP (following the structure of the RDA DMP Common Standard for machine-actionable Data Management Plans) . Each entry lists the FAIR principle, the original question, the corresponding maDMP path and the mapping status (`Mapped`, `Partially Mapped`, `Not Mapped`). During evaluation the mapping guides the checks that populate the reports listed above.

