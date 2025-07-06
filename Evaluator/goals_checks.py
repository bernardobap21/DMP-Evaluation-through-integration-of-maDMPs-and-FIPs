import validators
import requests

# Ask Tomasz if I should include more than these
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

################# Important fields should be declared
def check_completeness(dmp):
    required_fields_always = [
        "dmp_id.identifier",
        "dmp_id.type",
        "title",
        "description",
        "created",
        "modified",
        "ethical_issues_exist",
        "language",
        "contact.contact_id.identifier",
        "contact.contact_id.type",
        "contact.mbox",
        "contact.name",
        "project.title",
        "project.project_id.identifier",
        "project.project_id.type",
        "project.funding.funder_id.identifier",
        "project.funding.funder_id.type",
        "project.funding.grant_id.identifier",
        "project.funding.grant_id.type",
        "dataset"
    ]

    missing = []

    # Check nested fields
    def field_exists(data, path):
        keys = path.split(".")
        temp = data
        for key in keys:
            if isinstance(temp, list):
                temp = temp[0] if temp else {}
            if isinstance(temp, dict) and key in temp:
                temp = temp[key]
            else:
                return False
        return True

    # Check required fields
    for path in required_fields_always:
        if not field_exists(dmp, path):
            missing.append(path)

    datasets = dmp.get("dataset", [])
    dataset_missing = 0
    dataset_checked = 0

    for ds in datasets:
        dataset_checked += 1
        fields_to_check = [
            "dataset_id.identifier",
            "dataset_id.type",
            "title",
            "personal_data",
            "sensitive_data"
        ]
        for field in fields_to_check:
            if not field_exists(ds, field):
                missing.append(f"dataset.{dataset_checked-1}.{field}")
                dataset_missing += 1

        for dist in ds.get("distribution", []):
            dist_fields = [
                "title",
                "data_access"
            ]
            for field in dist_fields:
                if not field_exists(dist, field):
                    missing.append(f"dataset.{dataset_checked-1}.distribution.{field}")

            for lic in dist.get("license", []):
                if not field_exists(lic, "license_ref"):
                    missing.append(f"dataset.{dataset_checked-1}.distribution.license.license_ref")
                if not field_exists(lic, "start_date"):
                    missing.append(f"dataset.{dataset_checked-1}.distribution.license.start_date")

            if "host" in dist:
                if not field_exists(dist["host"], "title"):
                    missing.append(f"dataset.{dataset_checked-1}.distribution.host.title")
                if not field_exists(dist["host"], "url"):
                    missing.append(f"dataset.{dataset_checked-1}.distribution.host.url")

        for md in ds.get("metadata", []):
            if not field_exists(md, "language"):
                missing.append(f"dataset.{dataset_checked-1}.metadata.language")
            if "metadata_standard_id" in md:
                if not field_exists(md["metadata_standard_id"], "identifier"):
                    missing.append(f"dataset.{dataset_checked-1}.metadata.metadata_standard_id.identifier")
                if not field_exists(md["metadata_standard_id"], "type"):
                    missing.append(f"dataset.{dataset_checked-1}.metadata.metadata_standard_id.type")

    # total_fields = len(required_fields_always) + (dataset_checked * 5)  # 5 requirrd dataset fields per dataset
    # completeness_score = 1 - len(missing) / max(1, total_fields)

    # return round(completeness_score, 2), missing
    return  missing



########################
def check_accuracy(dmp):
    # Fields correctly filled
    issues = []
    datasets = dmp.get("dataset", [])

    for ds in datasets:
        title = ds.get("title", "Unknown dataset")

        # Check dataset identifier format
        dataset_id = ds.get("dataset_id", {}).get("identifier", "")
        if dataset_id and not validators.url(dataset_id):
            issues.append(f"[{title}] Invalid dataset identifier format: {dataset_id}")

        for dist in ds.get("distribution", []):
            # Check host URL
            host = dist.get("host", {})
            if host:
                url = host.get("url", "")
                if url and not validators.url(url):
                    issues.append(f"[{title}] Invalid host URL format: {url}")

            licenses = dist.get("license", [])
            for lic in licenses:
                lic_url = lic.get("license_ref", "")
                if lic_url and not validators.url(lic_url):
                    issues.append(f"[{title}] Invalid license URL format: {lic_url}")

    # score = 1 if not issues else max(0, 1 - 0.2 * len(issues))
    # return round(score, 2), issues

  
    return issues

########################
def check_availability(dmp):
    # are they accesible
    """Check that identifiers and URLs can be resolved online."""
    issues = []
    datasets = dmp.get("dataset", [])

    for ds in datasets:
        title = ds.get("title", "Unknown dataset")

        dataset_id = ds.get("dataset_id", {}).get("identifier", "")
        if dataset_id and validators.url(dataset_id):
            try:
                r = requests.head(dataset_id, allow_redirects=True, timeout=5)
                if r.status_code != 200:
                    issues.append(
                        f"[{title}] Dataset identifier not resolvable (status {r.status_code}): {dataset_id}"
                    )
            except Exception as e:
                issues.append(f"[{title}] Dataset identifier check error: {str(e)}")

        for dist in ds.get("distribution", []):
            host = dist.get("host", {})
            if host:
                url = host.get("url", "")
                if url and validators.url(url):
                    try:
                        r = requests.head(url, allow_redirects=True, timeout=5)
                        if r.status_code != 200:
                            issues.append(
                                f"[{title}] Host URL not resolvable (status {r.status_code}): {url}"
                            )
                    except Exception as e:
                        issues.append(f"[{title}] Host URL check error: {str(e)}")

            # Check license URL
            licenses = dist.get("license", [])
            for lic in licenses:
                lic_url = lic.get("license_ref", "")
                if lic_url and validators.url(lic_url):
                    try:
                        r = requests.head(lic_url, allow_redirects=True, timeout=5)
                        if r.status_code != 200:
                            issues.append(
                                f"[{title}] License URL not resolvable (status {r.status_code}): {lic_url}"
                            )
                    except Exception as e:
                        issues.append(f"[{title}] License URL check error: {str(e)}")

    # score = 1 if not issues else max(0, 1 - 0.2 * len(issues))
    return issues
    # return round(score, 2), issues

#######################
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
    return issues
    # return 1 if not issues else max(0, 1 - 0.15*len(issues)), issues

###########################
"""
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
"""

def run_goals_scoring(dmp):
    results = {}
    """
    c, c_issues = check_completeness(dmp)
    a, a_issues = check_accuracy(dmp)
    av, av_issues = check_availability(dmp)
    cs, cs_issues = check_consistency(dmp)
    """
    c_issues = check_completeness(dmp)
    a_issues = check_accuracy(dmp)
    av_issues = check_availability(dmp)
    cs_issues = check_consistency(dmp)
    # g, g_issues = check_guidance_compliance(dmp)

    """"
    results["completeness"] = {"score": round(c, 2), "issues": c_issues}
    results["accuracy"] = {"score": round(a, 2), "issues": a_issues}
    results["availability"] = {"score": round(av, 2), "issues": av_issues}
    results["consistency"] = {"score": round(cs, 2), "issues": cs_issues}
    # results["guidance_compliance"] = {"score": round(g, 2), "issues": g_issues}
    results["total_score"] = round((c + a + av + cs) / 4, 2)
    """

    results["completeness"] = {"issues": c_issues}
    results["accuracy"] = {"issues": a_issues}
    results["availability"] = {"issues": av_issues}
    results["consistency"] = {"issues": cs_issues}

    return results
