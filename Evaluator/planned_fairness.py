def check_planned_fairness(dmp):
    """Evaluate planned FAIRness of distributions in the maDMP."""
    test_results = []
    total_score = 0
    num_tests = 0

    #datasets = dmp.get("dmp", {}).get("dataset", [])
    datasets = dmp.get("dataset", [])


    for ds in datasets:
        title = ds.get("title", "Unnamed Dataset")
        for dist in ds.get("distribution", []):
            # === Test 1: data_access declared ===
            num_tests += 1
            data_access = dist.get("data_access")
            if data_access in ["open", "restricted", "closed"]:
                score = 1
                status = "pass"
                comment = ""
            else:
                score = 0
                status = "fail"
                comment = f"No or invalid access level for '{title}'"
            total_score += score
            test_results.append({
                "test_id": "planned_data_access",
                "test_name": "Access Level Declared",
                "test_description": "Checks if data access level is properly declared",
                "status": status,
                "score": score,
                "comment": comment
            })

            # Test 2: license exists
            num_tests += 1
            licenses = dist.get("license", [])
            has_license = bool(licenses and licenses[0].get("license_name"))
            if has_license:
                score = 1
                status = "pass"
                comment = ""
            else:
                score = 0
                status = "fail"
                comment = f"No license specified for '{title}'"
            total_score += score
            test_results.append({
                "test_id": "planned_license",
                "test_name": "License Specified",
                "test_description": "Checks if a license is planned",
                "status": status,
                "score": score,
                "comment": comment
            })

            # Test 3: format exists
            num_tests += 1
            if dist.get("format"):
                score = 1
                status = "pass"
                comment = ""
            else:
                score = 0
                status = "fail"
                comment = f"No file format planned for '{title}'"
            total_score += score
            test_results.append({
                "test_id": "planned_format",
                "test_name": "File Format Specified",
                "test_description": "Checks if file format is defined",
                "status": status,
                "score": score,
                "comment": comment
            })

            # Test 4: PID system declared
            num_tests += 1
            host = dist.get("host", {})
            pid_system = host.get("pid_system", [])
            if pid_system:
                score = 1
                status = "pass"
                comment = ""
            else:
                score = 0
                status = "fail"
                comment = f"No PID system defined for '{title}'"
            total_score += score
            test_results.append({
                "test_id": "planned_pid",
                "test_name": "PID System Declared",
                "test_description": "Checks if persistent identifier system is mentioned",
                "status": status,
                "score": score,
                "comment": comment
            })

            # Test 5: Supports versioning
            num_tests += 1
            versioning = host.get("supports_versioning")
            if versioning == "yes":
                score = 1
                status = "pass"
                comment = ""
            else:
                score = 0
                status = "fail"
                comment = f"Repository does not support versioning for '{title}'"
            total_score += score
            test_results.append({
                "test_id": "planned_versioning",
                "test_name": "Versioning Supported",
                "test_description": "Checks if the planned host supports versioning",
                "status": status,
                "score": score,
                "comment": comment
            })

    # Summary
    overall_score = round(total_score / num_tests, 2) if num_tests else 0
    return {
        "planned_fairness": {
            "score": overall_score,
            "test_results": test_results
        }
    }



