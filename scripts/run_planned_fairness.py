import sys
import os
import json
import argparse
from datetime import datetime

# Make sure Python finds your modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Evaluator.planned_fairness import check_planned_fairness
from Evaluator.ostrails_formatter import export_planned_fairness

# === CLI ARGUMENT PARSING ===
parser = argparse.ArgumentParser(description="Run planned FAIRness evaluation on a maDMP.")
parser.add_argument('--input', '-i', required=True, help='Path to the input maDMP JSON file')
parser.add_argument('--output', '-o', default='results/planned_fairness_ostrails.json', help='Path to save the output JSON-LD')

args = parser.parse_args()
input_path = args.input
output_path = args.output

# === Load maDMP ===
with open(input_path) as f:
    dmp = json.load(f)

# === Run the FAIRness Evaluation ===
result = check_planned_fairness(dmp)

# === Prepare Output ID ===
dmp_title = dmp.get("dmp", {}).get("title", "unknown").replace(" ", "_")
timestamp = datetime.now().strftime("%Y%m%d_%H%M")
dmp_id = f"{dmp_title}"  # optionally append _{timestamp}

# === Export OSTrails-compliant JSON-LD ===
export_planned_fairness(result["planned_fairness"]["test_results"], dmp_id=dmp_id, output_path=output_path)

print(f"✅ Export complete. Results saved to: {output_path}")
