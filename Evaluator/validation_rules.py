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

"""def check_personal_vs_sensitive(dataset):
    issues = []
    for ds in dataset:
        title = ds.get('title', 'Unnamed Dataset')
        personal = ds.get("personal_data", "").lower()
        sensitive = ds.get("sensitive_data", "").lower()
        if personal == "no" and sensitive == "yes":
            issues.append(f"Dataset '{title}' claims no personal data but is marked sensitive.")
    return issues"""

def check_distribution_integrity(datasets):
    issues = []
    for ds in datasets:
        title = ds.get("title", "Unknown")
        for dist in ds.get("distribution", []):
            # extract byte_size and check for None
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
    #personal_sensitive_issues = check_personal_vs_sensitive(datasets)
    distribution_integrity_issues = check_distribution_integrity(datasets)

    if access_license_issues:
        issues["access_vs_license"] = access_license_issues
    #if personal_sensitive_issues:
       # issues["personal_vs_sensitive"] = personal_sensitive_issues
    if distribution_integrity_issues:
        issues["distribution_integrity"] = distribution_integrity_issues

    return issues
