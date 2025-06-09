import json
import os
from datetime import datetime

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


    print(f"✅ Planned FAIRness (OSTrails format) saved to {output_path}")

