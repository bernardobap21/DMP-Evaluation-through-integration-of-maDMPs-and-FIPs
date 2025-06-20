from rdflib import Graph

def run_all_sparql_checks(graph):
    results = {}

    # License Present
    license_query = """
    ASK WHERE {
        ?distribution <https://w3id.org/dmp/terms/license> ?license .
    }
    """
    results["license_present"] = bool(graph.query(license_query))

    # Data Access Field Present
    data_access_query = """
    ASK WHERE {
        ?distribution <https://w3id.org/dmp/terms/dataAccess> ?access .
    }
    """
    results["data_access_present"] = bool(graph.query(data_access_query))

    # Dataset PID Exists
    pid_query = """
    ASK WHERE {
        ?dataset <https://w3id.org/dmp/terms/datasetID> ?pid .
    }
    """
    results["dataset_pid_present"] = bool(graph.query(pid_query))

    # Dataset Has Description
    dataset_desc_query = """
    ASK WHERE {
        ?dataset <http://purl.org/dc/terms/description> ?desc .
    }
    """
    results["dataset_description_present"] = bool(graph.query(dataset_desc_query))

    # Contributor Has ORCID
    orcid_query = """
    ASK WHERE {
        ?contributor <http://purl.org/dc/terms/identifier> ?id .
        FILTER CONTAINS(str(?id), "orcid.org")
    }
    """
    results["contributor_orcid_present"] = bool(graph.query(orcid_query))

    # Host Supports Versioning
    versioning_query = """
    ASK WHERE {
        ?host <https://w3id.org/dmp/terms/supportsVersioning> "yes" .
    }
    """
    results["host_supports_versioning"] = bool(graph.query(versioning_query))

    return results

def calculate_fair_score(sparql_results):
    total = len(sparql_results)
    passed = sum(1 for passed in sparql_results.values() if passed)
    score = round(passed / total, 2) if total > 0 else 0
    return {
        "total_checks": total,
        "passed_checks": passed,
        "fairness_score": score
    }

if __name__ == "__main__":
    g = Graph()
    g.parse("examples/ex9-dmp-long.ttl", format="turtle")

    results = run_all_sparql_checks(g)
    print("\n SPARQL Evaluation Results:")
    for check, status in results.items():
        print(f" {check.replace('_', ' ').capitalize()}: {status}")

    score_data = calculate_fair_score(results)
    print("\n FAIRness Score Summary:")
    print(f" Passed: {score_data['passed_checks']} / {score_data['total_checks']}")
    print(f" FAIRness Score: {score_data['fairness_score'] * 100:.1f}%")
