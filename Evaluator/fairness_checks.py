from urllib.parse import urlparse
import validators

# New to check licenses, etc.
def is_known_open_license(name):
    name = name.lower()
    keywords = [
        "cc",
        "creative commons",
        "creativecommons",
        "mit",
        "open",
        "gnu",
        "gpl",
        "apache",
        "bsd",
    ]
    return any(keyword in name for keyword in keywords)

def check_completeness(dmp):
    required_fields = [
        "dmp_id.identifier",
        "contact.name",
        "dataset",
        "dataset[0].distribution",
        "dataset[0].distribution[0].license",
    ]
    missing = []
    for path in required_fields:
        keys = path.replace('[0]', "").split(".")
        temp = dmp
        for key in keys:
            if isinstance(temp, list):
                temp = temp[0] if temp else {}
            temp = temp.get(key) if isinstance(temp, dict) else None
            if temp is None:
                missing.append(path)
                break
    return 1 - len(missing)/len(required_fields), missing

def check_accuracy(dmp):
    issues = []
    datasets = dmp.get("dataset", [])
    for ds in datasets:
        for dist in ds.get("distribution", []):
            # Check host URL
            host = dist.get("host", {})
            if host:
                url = host.get("url", "")
                if url and not validators.url(url):
                    issues.append(f"Invalid host URL: {url}")
            # Check license
            licenses = dist.get("license", [])
            for lic in licenses:
                url = lic.get("license_ref", "")
                if url and not validators.url(url):
                    issues.append(f"Invalid license URL: {url}")
    return 1 if not issues else max(0, 1 - 0.2*len(issues)), issues

def check_consistency(dmp):
    issues = []
    for ds in dmp.get("dataset", []):
        for dist in ds.get("distribution", []):
            access = dist.get("data_access", "")
            licenses = dist.get("license", [])
            has_license = any(
                lic.get("license_name") or lic.get("license_ref") for lic in licenses
            )
            if access == "open" and not has_license:
                issues.append(f"{ds.get('title')} is open but lacks a license.")
            if not dist.get("byte_size"):
                issues.append(f"{ds.get('title')} is missing byte_size.")
            if not dist.get("format"):
                issues.append(f"{ds.get('title')} is missing format.")
    return 1 if not issues else max(0, 1 - 0.15*len(issues)), issues

def check_guidance_compliance(dmp):
    issues = []
    lang = dmp.get("language")
    if lang:
        if lang not in ["en", "eng"]:
            issues.append(f"Language '{lang}' not standard.")
    else:
        issues.append("Language missing.")
    for ds in dmp.get("dataset", []):
        for dist in ds.get("distribution", []):
            for lic in dist.get("license", []):
                lic_name = lic.get("license_name") or lic.get("license_ref", "")
                if not is_known_open_license(lic_name):
                    issues.append(f"License '{lic_name}' may not be FAIR-compliant.")
    return 1 if not issues else max(0, 1 - 0.2 * len(issues)), issues

def run_fairness_scoring(dmp):
    results = {}
    c, c_issues = check_completeness(dmp)
    a, a_issues = check_accuracy(dmp)
    cs, cs_issues = check_consistency(dmp)
    g, g_issues = check_guidance_compliance(dmp)

    results["completeness"] = {"score": round(c, 2), "issues": c_issues}
    results["accuracy"] = {"score": round(a, 2), "issues": a_issues}
    results["consistency"] = {"score": round(cs, 2), "issues": cs_issues}
    results["guidance_compliance"] = {"score": round(g, 2), "issues": g_issues}
    results["total_score"] = round((c + a + cs + g) / 4, 2)

    return results
