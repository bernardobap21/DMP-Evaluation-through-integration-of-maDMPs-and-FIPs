import argparse
import os
import json

# Import your own modules
from FIP_Mapping.mapping import load_mapping
from FIP_Mapping.utils import transform_mapping
from Evaluator.evaluator import (
    load_dmp,
    evaluate_dmp_against_fip,
    summarize_results,
    save_evaluation_results,
    save_recommendations
)

def main():
    parser = argparse.ArgumentParser(description="Evaluate a maDMP against a FIP mapping.")
    parser.add_argument('--input', required=True, help='Path to the maDMP JSON file')
    parser.add_argument('--mapping', required=True, help='Path to the FIP mapping JSON file')
    parser.add_argument('--output', required=True, help='Output folder to save evaluation results')

    args = parser.parse_args()

    # Create output directory if it doesn't exist
    os.makedirs(args.output, exist_ok=True)

    # Load input files
    dmp = load_dmp(args.input)
    mapping_raw = load_mapping(args.mapping)
    mapping = transform_mapping(mapping_raw)   # Transform after loading!

    # Evaluate
    evaluation_results = evaluate_dmp_against_fip(dmp, mapping)

    # Summarize
    present, total = summarize_results(evaluation_results)
    print(f"✅ Evaluation Complete: {present}/{total} fields present.")

    # Prepare filenames
    base_filename = os.path.splitext(os.path.basename(args.input))[0]
    csv_output = os.path.join(args.output, f"{base_filename}_evaluation.csv")
    txt_output = os.path.join(args.output, f"{base_filename}_recommendations.txt")

    # Save outputs
    save_evaluation_results(evaluation_results, csv_output)
    save_recommendations(evaluation_results, txt_output)

    print(f"📄 Saved evaluation report to: {csv_output}")
    print(f"📝 Saved recommendations to: {txt_output}")

if __name__ == "__main__":
    main()
