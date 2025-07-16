import argparse
import os
import json

from FIP_Mapping.mapping import load_mapping
from FIP_Mapping.utils import transform_mapping
from Evaluator.goals_checks import run_goals_scoring
from Evaluator.validation_rules import validate_metadata_intentions
from Evaluator.planned_fairness import check_planned_fairness
from Evaluator.ostrails_formatter import export_fip_results, DEFAULT_VERSION
from Evaluator.evaluator import (
    load_dmp,
    evaluate_dmp_against_fip,
    summarize_results,
    save_evaluation_results,
    save_recommendations,
    save_compliance_table 
)


def main():
    parser = argparse.ArgumentParser(description="Evaluate a maDMP against a FIP mapping.")
    parser.add_argument('--input', required=True, help='Path to the maDMP JSON file')
    parser.add_argument('--mapping', required=True, help='Path to the FIP mapping JSON file')
    parser.add_argument('--output', required=True, help='Output folder to save evaluation results')

    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    # Load the maDMP and FIP mapping
    dmp = load_dmp(args.input)
    mapping_raw = load_mapping(args.mapping)
    mapping = transform_mapping(mapping_raw)
    metric_versions = {
        item["FIP_question"]: item.get("Metric_version", DEFAULT_VERSION)
        for item in mapping_raw.get("FIP_maDMP_Mapping", [])
    }

    evaluation_results = evaluate_dmp_against_fip(dmp, mapping)

    # Transform into OSTrails TestResult format
    ftr_ready = []
    for idx, r in enumerate(evaluation_results, start=1):
        metric_id = f"FIP{str(idx).zfill(2)}.Q{idx}"
        benchmark = r.get("allowed_values", [])
        if benchmark and not isinstance(benchmark, list):
            benchmark = [benchmark]
        ###
        fair_principle = r.get("FAIR_principle")
        ###

        field_val = json.dumps(r.get("field_value"), ensure_ascii=False)
        comment = (
            f"Field status: {r['field_status']}; maDMP value: {field_val}; "
            f"compliance: {r['compliance_status']}"
        )

        status = (
            "pass" if r["field_status"] == "Present" and r["compliance_status"] == "Compliant" else "fail"
        )

        ftr_ready.append({
            "metric_id": metric_id,
            "metric_label": r["FIP_question"],
            "test_id": f"Test_{metric_id}",
            "benchmark": benchmark,
            ###
            "fair_principle": fair_principle,
            ###
            "comment": comment,
            "subject": r["maDMP_field"],
            "status": status,
            "metric_version": metric_versions.get(r["FIP_question"], DEFAULT_VERSION),
        })


    present, compliant, total = summarize_results(evaluation_results)
    print(f"Evaluation Complete: \n{present}/{total} fields present. \n{compliant}/{total} compliant.")

    base_filename = os.path.splitext(os.path.basename(args.input))[0]
    #csv_output = os.path.join(args.output, f"{base_filename}_mapping_report.csv")
    txt_output = os.path.join(args.output, f"{base_filename}_recommendations.txt")

    #save_evaluation_results(evaluation_results, csv_output)
    save_recommendations(evaluation_results, txt_output)

    ###########
    compliance_output = os.path.join(args.output, f"{base_filename}_compliance_table.csv")
    save_compliance_table(evaluation_results, compliance_output)
    print(f"Compliance details saved to: {compliance_output}")

    #print(f"Saved evaluation report to: {csv_output}")
    print(f"Saved recommendations to: {txt_output}")

    # Export JSON-LD according to OSTrails
    fip_jsonld = export_fip_results(
        ftr_ready,
        dmp_id=base_filename,
        dmp_title=dmp.get("title", base_filename),
        output_dir=args.output,
    )
    print(f"OSTrails Format results saved to: {fip_jsonld}")

    # Run FAIRness scoring and validation
    goals_results = run_goals_scoring(dmp)

    goals_output = os.path.join(args.output, f"{base_filename}_goals_check.json")
    with open(goals_output, 'w', encoding='utf-8') as file:
        json.dump(goals_results, file, indent=2)

    print(f"Goals evaluation results saved to: {goals_output}")

    # Validate metadata 
    metadata_issues = validate_metadata_intentions(dmp)

    validation_output = os.path.join(args.output, f"{base_filename}_metadata_validation.json")
    with open(validation_output, 'w', encoding='utf-8') as file:
        json.dump(metadata_issues, file, indent=2)

    print(f"Metadata intention validation results saved to: {validation_output}")

    # Check planned FAIRness
    planned_result = check_planned_fairness(dmp)
    planned_output = os.path.join(args.output, f"{base_filename}_planned_fairness.json")
    with open(planned_output, 'w') as f:
        json.dump(planned_result, f, indent=2)

    print(f"Planned FAIRness evaluation results saved to: {planned_output}")

       

if __name__ == "__main__":
    main()
