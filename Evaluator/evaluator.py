import json
import csv

def load_dmp(file_path):
    """Load a maDMP file and enter into 'dmp' node if it exists."""
    with open(file_path, 'r') as file:
        dmp = json.load(file)
    # Check if there's a top-level "dmp" field
    if "dmp" in dmp:
        dmp = dmp["dmp"]
    return dmp

def evaluate_dmp_against_fip(dmp, mapping_dict):
    """Check how well the DMP satisfies the FIP-mapped fields"""
    results = []
    for question, details in mapping_dict.items():
        field_path = details["maDMP_field"]
        status = "Not Present"

        # Skip if not mapped
        if not field_path:
            results.append((question, "Not Mapped", None))
            continue

        # Traverse nested keys safely
        value = dmp
        for key in field_path.split('.'):
            if isinstance(value, dict) and key in value:
                value = value[key]
            elif isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                value = value[0].get(key)
            else:
                value = None
                break

        if value is not None:
            status = "Present"
        results.append((question, details["Mapping_status"], status))

    return results

def summarize_results(results):
    """Simple summary printout"""
    present = sum(1 for _, _, status in results if status == "Present")
    total = len(results)
    print(f"{present}/{total} fields present in the maDMP.")
    return present, total


def save_evaluation_results(results, output_path):
    """Save evaluation results as CSV"""
    with open(output_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["FIP Question", "Mapping Status", "Field Status"])
        for row in results:
            writer.writerow(row)

def save_recommendations(results, output_path):
    """Save a simple recommendations TXT file based on missing fields"""
    recommendations = []
    for question, mapping_status, field_status in results:
        if field_status != "Present":
            recommendations.append(f"- Improve or add metadata for: {question} (Mapping status: {mapping_status})")

    if not recommendations:
        recommendations.append(" All mapped fields are present! No missing information detected.")

    with open(output_path, mode='w', encoding='utf-8') as file:
        for line in recommendations:
            file.write(line + "\n")