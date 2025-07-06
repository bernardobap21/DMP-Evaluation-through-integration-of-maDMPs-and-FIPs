import json
from datetime import datetime
import os

"""""
def export_planned_fairness(test_results, dmp_id, output_path):
    output = {
        "@context": "https://w3id.org/ostrails/fair-assessment/context",
        "@type": "AssessmentResult",
        "evaluated_resource": dmp_id,
        "date": datetime.now().isoformat(),
        "results": []
    }

    for test in test_results:
        output["results"].append({
            "@type": "TestResult",
            "test_id": test.get("test_id"),
            "test_name": test.get("test_name"),
            "test_description": test.get("test_description"),
            "test_status": test.get("status"),
            "score": test.get("score"),
            "comment": test.get("comment", "")
        })

    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)


    print(f"Planned FAIRness (OSTrails format) saved to {output_path}")
"""

def export_planned_fairness(test_results, dmp_id, output_path):
    output = {
        "@context": "https://w3id.org/ostrails/fair-assessment/context",
        "@type": "AssessmentResult",
        "evaluated_resource": dmp_id,
        "date": datetime.now().isoformat(),
        "results": []
    }

    for test in test_results:
        output["results"].append({
            "@type": "TestResult",
            "test_id": test.get("test_id"),
            "test_name": test.get("test_name"),
            "test_description": test.get("test_description"),
            "test_status": test.get("status"),
            "comment": test.get("comment", "")
        })

    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)


    print(f"Planned FAIRness (OSTrails format) saved to {output_path}")


def export_fip_results(results, dmp_id, dmp_title, output_dir):
    """Export FIP evaluation results in OSTrails TestResultSet JSON-LD format.

    Parameters
    ----------
    results : list of dict
        Each dictionary should contain `metric_id`, `metric_label`, `test_id`,
        `benchmark`, `comment` and `subject` keys.
    dmp_id : str
        Identifier for the DMP being evaluated.
    dmp_title : str
        Human readable DMP title used in the TestResultSet title.
    output_dir : str
        Directory where the JSON-LD file will be written.
    """

    out = {
        "@context": "https://w3id.org/ftr/context.jsonld",
        "@type": "ftr:TestResultSet",
        "dcterms:identifier": dmp_id,
        "dcterms:title": f"Evaluation results for DMP: {dmp_title}",
        "ftr:hasMember": [],
    }

    for res in results:
        test_block = {
            "@type": "ftr:TestResult",
            "metric_id": res.get("metric_id"),
            "metric_label": res.get("metric_label"),
            "test_id": res.get("test_id"),
            "benchmark": res.get("benchmark", []),
            "comment": res.get("comment", ""),
            "subject": res.get("subject"),
        }
        out["ftr:hasMember"].append(test_block)

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{dmp_id}_ostrails_results.jsonld")
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)

    return output_path
