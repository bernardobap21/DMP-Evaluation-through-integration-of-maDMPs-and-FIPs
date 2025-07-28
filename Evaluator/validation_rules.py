# Recognize formats and vocabularies
import re
from urllib.parse import urlparse, urlunparse
import requests

# Checks for metadata 
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

def _normalize_url(url: str) -> str:
    """Normalize a URL for comparison."""
    if not isinstance(url, str):
        return ""
    url = url.strip()
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip('/')
    if path.endswith('/legalcode'):
        path = path[:-9].rstrip('/')
    return urlunparse((scheme, netloc, path, '', '', ''))

_SPDX_CACHE = None


def _to_spdx_id(label: str) -> str:
    """Convert common license labels to SPDX identifiers."""
    return label.strip().replace(" ", "-")


def is_license_compliant(madmp_url: str, spdx_id: str) -> bool:
    """Check if the given URL corresponds to the SPDX license."""
    global _SPDX_CACHE
    if _SPDX_CACHE is None:
        try:
            resp = requests.get("https://spdx.org/licenses/licenses.json", timeout=10)
            _SPDX_CACHE = resp.json()
        except Exception:
            return False

    data = _SPDX_CACHE
    spdx_id = _to_spdx_id(spdx_id)
    

    for lic in data.get("licenses", []):
        if lic.get("licenseId") == spdx_id:
            normalized_input = _normalize_url(madmp_url)
            for url in lic.get("seeAlso", []):
                if normalized_input == _normalize_url(url):
                    return True
            break
    return False



def detect_identifier_type(identifier, allowed_values=None):
    if not isinstance(identifier, str):
        return "Unknown"

    # Normalize
    raw_identifier = identifier.strip()
    lower_identifier = raw_identifier.lower()

    # Patterns
    patterns = {
        "DOI": r"^https?://doi\.org/10\.\d{4,9}/[-._;()/:a-z0-9]+$",
        "Crossref (DOI)": r"^https?://doi\.crossref\.org/10\.\d{4,9}/[-._;()/:a-z0-9]+$",
        "URI": r"^https?://[^\s]+$",
        "HTTPS": r"^https://.*$",
        "B2HANDLE": r"^hdl:\d+/.+$",
        "Handle": r"^https:\/\/hdl\.handle\.net\/\d+\/[A-Za-z0-9.\-]+$",
        "dPIDs": r"^[a-f0-9-]{36}$",
        "UUID": r"^[a-f0-9-]{36}$",
        "REST": r"^(GET|POST|PUT|DELETE).*"
    }

    # If allowed_values are provided, prioritize matching these first
    if allowed_values:
        for val in allowed_values:
            if is_license_compliant(raw_identifier, val):
                return val
            pattern = patterns.get(val)
            if pattern and re.match(pattern, lower_identifier, re.I):
                return val


    known_labels = [
        "Schema.org", "DCAT", "Dublin Core", "DataCite", "GBIF search engine",
        "Global Biotic Interactions", "Open Data", "Open", "OAuth 2.0", "GBIF local account",
        "DwC-A", "JSON", "XMLS", "RDFS", "EML", "DwC",
        "Plant Pollinator Vocabulary", "Relations Ontology", "PROV-O",
    ]
    """
        "CC0 1.0", "CC-BY 4.0", "CC BY-NC 4.0",
    ]
    """


    # Match patterns
    for id_type, pattern in patterns.items():
        if re.match(pattern, lower_identifier, re.I):
            return id_type

    # Exact match to label
    for label in known_labels:
        if lower_identifier == label.strip().lower():
            return label

    return "Unknown"


# allowed-value checker
def is_allowed_value(field_value, allowed_values):
    
    def check_one(val):
        detected = detect_identifier_type(val, allowed_values)
        return detected in allowed_values or val in allowed_values

    if isinstance(field_value, list):
        return all(check_one(v) for v in field_value)
    return check_one(field_value)
