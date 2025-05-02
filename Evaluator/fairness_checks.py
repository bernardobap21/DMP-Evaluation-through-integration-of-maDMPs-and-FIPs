import validators

def check_completeness(dmp):
    """Check if required fields for FAIR principles are filled."""
    required_fields = [
        "dmp_id.identifier",
        "contact.name",
        "dataset",
        "dataset[0].distribution",
        "dataset[0].distribution[0].license",
    ]
    missing_fields = []
    for path in required_fields:
        keys = path.replace('[0]', '').split('.')
        temp = dmp
        for key in keys:
            if isinstance(temp, list):
                temp = temp[0] if temp else {}
            temp = temp.get(key) if isinstance(temp, dict) else None
            if temp is None:
                missing_fields.append(path)
                break
    completeness_score = 1 - len(missing_fields)/len(required_fields)
    return completeness_score, missing_fields

def check_accuracy(dmp):
    """Validate URLs, licenses, identifiers."""
    issues = []
    datasets = dmp.get("dataset", [])
    for ds in datasets:
        distributions = ds.get("distribution", [])
        for dist in distributions:
            license_info = dist.get("license", [{}])[0]
            license_ref = license_info.get("license_ref", "")
            if license_ref and not validators.url(license_ref):
                issues.append(f"Invalid license URL: {license_ref}")
            host_info = dist.get("host", {})
            host_url = host_info.get("url", "")
            if host_url and not validators.url(host_url):
                issues.append(f"Invalid host URL: {host_url}")

    accuracy_score = 1 if not issues else max(0, 1 - len(issues)*0.25)
    return accuracy_score, issues

def check_consistency(dmp):
    """Check logical consistency in the dataset metadata."""
    issues = []
    datasets = dmp.get("dataset", [])
    for ds in datasets:
        for dist in ds.get("distribution", []):
            data_access = dist.get("data_access")
            license_exists = "license" in dist and dist["license"]
            if data_access == "open" and not license_exists:
                issues.append(f"Dataset '{ds.get('title')}' is marked open but has no license.")
    consistency_score = 1 if not issues else max(0, 1 - len(issues)*0.25)
    return consistency_score, issues

def check_guidance_compliance(dmp):
    """Check if vocabularies and formats follow known standards (simple check)."""
    issues = []
    if "language" in dmp and dmp["language"] not in ["eng", "en"]:
        issues.append(f"Non-standard language code: {dmp['language']}")

    guidance_score = 1 if not issues else max(0, 1 - len(issues)*0.25)
    return guidance_score, issues

def run_fairness_scoring(dmp):
    """Run all FAIR checks and compile scores."""
    results = {}
    completeness, comp_issues = check_completeness(dmp)
    accuracy, acc_issues = check_accuracy(dmp)
    consistency, cons_issues = check_consistency(dmp)
    guidance, guid_issues = check_guidance_compliance(dmp)

    results["completeness"] = {"score": completeness, "issues": comp_issues}
    results["accuracy"] = {"score": accuracy, "issues": acc_issues}
    results["consistency"] = {"score": consistency, "issues": cons_issues}
    results["guidance_compliance"] = {"score": guidance, "issues": guid_issues}

    total_score = (completeness + accuracy + consistency + guidance) / 4
    results["total_score"] = total_score

    return results
