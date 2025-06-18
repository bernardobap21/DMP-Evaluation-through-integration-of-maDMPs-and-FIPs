import re

# Existing generic checks...
def check_access_vs_license(dataset):
    issues = []
    for ds in dataset:
        title = ds.get('title', 'Unnamed Dataset')
        for dist in ds.get("distribution", []):
            access = dist.get("data_access", "").lower()
            license_present = bool(dist.get("license"))
            if access == "open" and not license_present:
                issues.append(f"Dataset '{title}' marked as open access but has no license.")
    return issues

def check_personal_vs_sensitive(dataset):
    issues = []
    for ds in dataset:
        title = ds.get('title', 'Unnamed Dataset')
        personal = ds.get("personal_data", "").lower()
        sensitive = ds.get("sensitive_data", "").lower()
        if personal == "yes" and sensitive == "no":
            issues.append(f"Dataset '{title}' claims no sensitive data but contains personal data.")
    return issues

def check_distribution_integrity(datasets):
    issues = []
    for ds in datasets:
        title = ds.get("title", "Unknown")
        for dist in ds.get("distribution", []):
            byte_size = dist.get("byte_size")
            if byte_size is None:
                issues.append(f"Dataset '{title}' has a distribution with missing byte_size.")
            elif byte_size <= 0:
                issues.append(f"Dataset '{title}' has invalid byte_size: {byte_size}")
    return issues

def validate_metadata_intentions(dmp):
    issues = {}
    datasets = dmp.get("dataset", [])
    access_license_issues = check_access_vs_license(datasets)
    personal_sensitive_issues = check_personal_vs_sensitive(datasets)
    distribution_integrity_issues = check_distribution_integrity(datasets)

    if access_license_issues:
        issues["access_vs_license"] = access_license_issues
    if personal_sensitive_issues:
        issues["personal_vs_sensitive"] = personal_sensitive_issues
    if distribution_integrity_issues:
        issues["distribution_integrity"] = distribution_integrity_issues

    return issues

# Enhanced detect_identifier_type to recognize a wide range of formats and vocabularies
import re

def detect_identifier_type(identifier):
    if not isinstance(identifier, str):
        return "Unknown"

    # Normalize
    identifier = identifier.strip().lower()

    # Patterns
    patterns = {
        "DOI": r"^https?://doi\.org/10\.\d{4,9}/[-._;()/:a-z0-9]+$",
        "URI": r"^https?://[^\s]+$",
        "HTTPS": r"^https://.*$",
        "B2HANDLE": r"^hdl:\d+/.+$",
        "dPIDs": r"^[a-f0-9-]{36}$",
        "UUID": r"^[a-f0-9-]{36}$",
        "REST": r"^(GET|POST|PUT|DELETE).*"
    }

    known_labels = [
        "Schema.org", "DCAT", "Dublin Core", "DataCite", "GBIF search engine",
        "Global Biotic Interactions", "Open Data", "OAuth 2.0", "GBIF local account",
        "DwC-A", "JSON", "XMLS", "RDFS", "EML", "DwC",
        "Plant Pollinator Vocabulary", "Relations Ontology",
        "CC0 1.0", "CC-BY 4.0", "CC BY-NC 4.0", "PROV-O"
    ]

    # Match patterns
    for id_type, pattern in patterns.items():
        if re.match(pattern, identifier, re.I):
            return id_type

    # Exact match to label
    for label in known_labels:
        if identifier == label.strip().lower():
            return label

    return "Unknown"


# Updated generic allowed-value checker
def is_allowed_value(field_value, allowed_values):
    """
    Checks if a field value (string or list) matches any allowed types/value names.
    """
    def check_one(val):
        detected = detect_identifier_type(val)
        return detected in allowed_values or val in allowed_values

    if isinstance(field_value, list):
        return all(check_one(v) for v in field_value)
    return check_one(field_value)
