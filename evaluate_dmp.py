import argparse
import os
import json

from FIP_Mapping.mapping import load_mapping
from FIP_Mapping.utils import transform_mapping
from Evaluator.goals_checks import run_goals_scoring
from Evaluator.validation_rules import validate_metadata_intentions
from Evaluator.ostrails_formatter import export_fip_results, DEFAULT_VERSION
from Evaluator.evaluator import (
    load_dmp,
    evaluate_dmp_against_fip,
    summarize_results,
    save_recommendations,
    save_compliance_table, 
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
    fip_version = mapping_raw.get("FIP_Version", DEFAULT_VERSION)

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
            if r.get("compliance_status") == "Not Applicable":
                status_vals.append("indeterminate")
                continue
            if not r.get("allowed_values"):
                status_vals.append("indeterminate")
            else:
                status_vals.append(
                    "pass" if r["field_status"] == "Present" and comp == "Compliant" else "fail"
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
            "log_value": log_val,
            "subject": r["DCS_field"],
            "status": status_vals,
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
        metric_version=fip_version,
    )
    print(f"OSTrails Format results saved to: {fip_jsonld}")

    # Run goals checks validation
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

    print(f"Metadata validation results saved to: {validation_output}")    

if __name__ == "__main__":
    main()
