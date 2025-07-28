import json
import csv
from .validation_rules import is_allowed_value

def _collect_values(data, path_parts):
    """Recursively collect all values for the given path parts."""
    if not path_parts:
        return [data]

    key = path_parts[0]
    remaining = path_parts[1:]

    results = []
    if isinstance(data, dict):
        if key in data:
            results.extend(_collect_values(data[key], remaining))
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, (dict, list)):
                if isinstance(item, dict) and key not in item:
                    continue
                value = item[key] if isinstance(item, dict) else item
                results.extend(_collect_values(value, remaining))
    return results


def load_dmp(file_path):
    with open(file_path, 'r') as file:
        dmp = json.load(file)
    if "dmp" in dmp:
        dmp = dmp["dmp"]
    return dmp

def evaluate_dmp_against_fip(dmp, mapping_dict):
    results = []
    for question, details in mapping_dict.items():
        field_path = details.get("DCS_field") or details.get("maDMP_field", "")
        allowed_values = details.get("Allowed_values", [])
        mapping_status = details.get("Mapping_status", "Unmapped")
        ####
        fair_principle = details.get("FAIR_principle")

        # Default values
        field_status = "Not Present"
        compliance_status = "Not Applicable"
        field_value = None

        if not field_path:
            results.append({
                "FIP_question": question,
                "DCS_field": None,
                "field_value": None,
                "allowed_values": allowed_values,
                "mapping_status": mapping_status,
                #####
                "FAIR_principle": fair_principle,
                "field_status": field_status,
                "compliance_status": compliance_status
            })
            continue

        # Extract all matching values
        values = _collect_values(dmp, field_path.split('.')) if field_path else []

        if values:
            field_status = "Present"
            field_value = values
            if allowed_values:
                compliance_list = [
                    "Compliant" if is_allowed_value(v, allowed_values) else "Non-compliant"
                    for v in values
                ]
                compliance_status = "Compliant" if all(cs == "Compliant" for cs in compliance_list) else "Non-compliant"
            else:
                compliance_list = []
        else:
            compliance_list = []
            if allowed_values:
                compliance_status = "Missing value"

        results.append({
            "FIP_question": question,
            "DCS_field": field_path,
            "field_value": field_value,
            "allowed_values": allowed_values,
            "mapping_status": mapping_status,
            #####
            "FAIR_principle": fair_principle,
            "field_status": field_status,
            "compliance_status": compliance_status,
            "compliance_list": compliance_list
        })

    return results

def summarize_results(results):
    present = sum(1 for r in results if r["field_status"] == "Present")
    compliant = 0
    for r in results:
        cs = r.get("compliance_status")
        if isinstance(cs, list):
            if cs and all(x == "Compliant" for x in cs):
                compliant += 1
        else:
            if cs == "Compliant":
                compliant += 1
    total = len(results)
    #print(f"{present}/{total} fields present in the maDMP.")
    #print(f"{compliant}/{total} fields compliant with allowed values.")
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
                f"- Improve or add metadata for: {r['FIP_question']} (Field: {r['DCS_field']}, "
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
        writer.writerow(["FIP Question", "DCS Field", "maDMP Value", "Accepted Values", "Compliant"])
        for r in results:
            allowed_values = r["allowed_values"]
            if isinstance(allowed_values, list):
                allowed_str = ", ".join(allowed_values)
            else:
                allowed_str = allowed_values

            comp = r.get("compliance_list") or r.get("compliance_status")
            if not allowed_values:
                compliant = "No choice made by community"
            else:
                if isinstance(comp, list):
                    entries = ["Yes" if c == "Compliant" else "No" for c in comp]
                    compliant = f"[{', '.join(entries)}]"
                else:
                    compliant = "Yes" if comp == "Compliant" else "No"


            writer.writerow([
                r["FIP_question"],
                r["DCS_field"],
                json.dumps(r["field_value"], ensure_ascii=False),
                allowed_str,
                compliant
            ])
