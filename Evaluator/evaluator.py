import json
import csv
from .validation_rules import is_allowed_value

def load_dmp(file_path):
    with open(file_path, 'r') as file:
        dmp = json.load(file)
    if "dmp" in dmp:
        dmp = dmp["dmp"]
    return dmp

def evaluate_dmp_against_fip(dmp, mapping_dict):
    results = []
    for question, details in mapping_dict.items():
        field_path = details.get("maDMP_field", "")
        allowed_values = details.get("Allowed_values", [])
        mapping_status = details.get("Mapping_status", "Unmapped")

        # Default values
        field_status = "Not Present"
        compliance_status = "Not Applicable"
        field_value = None

        if not field_path:
            results.append({
                "FIP_question": question,
                "maDMP_field": None,
                "field_value": None,
                "allowed_values": allowed_values,
                "mapping_status": mapping_status,
                "field_status": field_status,
                "compliance_status": compliance_status
            })
            continue

        # Resolve field value
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
            field_status = "Present"
            field_value = value
            if allowed_values:
                compliance_status = "Compliant" if is_allowed_value(value, allowed_values) else "Non-compliant"
        elif allowed_values:
            compliance_status = "Missing value"

        results.append({
            "FIP_question": question,
            "maDMP_field": field_path,
            "field_value": field_value,
            "allowed_values": allowed_values,
            "mapping_status": mapping_status,
            "field_status": field_status,
            "compliance_status": compliance_status
        })

    return results

def summarize_results(results):
    present = sum(1 for r in results if r["field_status"] == "Present")
    compliant = sum(1 for r in results if r["compliance_status"] == "Compliant")
    total = len(results)
    print(f"{present}/{total} fields present in the maDMP.")
    print(f"{compliant}/{total} fields compliant with allowed values.")
    return present, compliant, total

def save_evaluation_results(results, output_path):
    with open(output_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["FIP Question", "Mapping Status", "Field Status", "Compliance Status"])
        for r in results:
            writer.writerow([
                r["FIP_question"],
                r["mapping_status"],
                r["field_status"],
                r["compliance_status"]
            ])

def save_recommendations(results, output_path):
    recommendations = []
    for r in results:
        if r["field_status"] != "Present" or r["compliance_status"] == "Non-compliant":
            recommendations.append(
                f"- Improve or add metadata for: {r['FIP_question']} (Field: {r['maDMP_field']}, "
                f"Compliance: {r['compliance_status']})"
            )
    if not recommendations:
        recommendations.append("All mapped fields are present and compliant!")

    with open(output_path, mode='w', encoding='utf-8') as file:
        for line in recommendations:
            file.write(line + "\n")

def save_compliance_table(results, output_path):
    with open(output_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["FIP Question", "maDMP Field", "maDMP Value", "Accepted Values", "Compliant"])
        for r in results:
            writer.writerow([
                r["FIP_question"],
                r["maDMP_field"],
                json.dumps(r["field_value"], ensure_ascii=False),
                ", ".join(r["allowed_values"]),
                "Yes" if r["compliance_status"] == "Compliant" else "No"
            ])
