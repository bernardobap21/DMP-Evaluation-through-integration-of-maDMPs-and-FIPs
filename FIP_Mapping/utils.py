def transform_mapping(mapping_data):
    return {
        item["FIP_question"]: {
            "FAIR_principle": item["FAIR_principle"],
            "maDMP_field": item["maDMP_field"],
            "Mapping_status": item["Mapping_status"],
            "Comments": item["Comments"]
        }
        for item in mapping_data["FIP_maDMP_Mapping"]
    }

def get_mapped_status(mapping_dict, status):
    return {
        question: details
        for question, details in mapping_dict.items()
        if details["Mapping_status"] == status
    }
