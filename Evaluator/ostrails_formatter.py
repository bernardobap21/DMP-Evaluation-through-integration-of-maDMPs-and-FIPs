import json
from datetime import datetime
import os

def export_planned_fairness(test_results, dmp_id, output_path):
    output = {
        "@context": "https://w3id.org/ostrails/fair-assessment/context",
        "@type": "AssessmentResult",
        "evaluated_resource": dmp_id,
        "date": datetime.now().isoformat(),
        "results": []
    }

    for test in test_results:
        output["results"].append({
            "@type": "TestResult",
            "test_id": test.get("test_id"),
            "test_name": test.get("test_name"),
            "test_description": test.get("test_description"),
            "test_status": test.get("status"),
            "comment": test.get("comment", "")
        })

    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)


    print(f"Planned FAIRness (OSTrails format) saved to {output_path}")


def export_fip_results(results, dmp_id, dmp_title, output_dir):
    
    graph = []

    result_set_id = f"#{dmp_id}_results"
    result_set = {
        "@id": result_set_id,
        "@type": "ftr:TestResultSet",
        "dcterms:identifier": dmp_id,
        "dcterms:title": f"Evaluation results for DMP: {dmp_title}",
        "dcterms:license": "https://creativecommons.org/publicdomain/zero/1.0/",
        "prov:hadMember": [],
    }
    graph.append(result_set)

    for res in results:
        metric_uri = f"#{res['metric_id']}"
        metric = {
            "@id": metric_uri,
            "@type": "dqv:Metric",
            "dcterms:identifier": res["metric_id"],
            "dcterms:title": res["metric_label"],
            "dcterms:description": res["metric_label"],
        }
        graph.append(metric)

        test_uri = f"#{res['test_id']}"
        test_node = {
            "@id": test_uri,
            "@type": "ftr:Test",
            "dcterms:identifier": res["test_id"],
            "dcterms:title": res["metric_label"],
            "dcterms:description": f"Check field {res['subject']}",
            "ftr:testsMetric": metric_uri,
            "ftr:hasBenchmark": [],
        }
        graph.append(test_node)

        for idx, val in enumerate(res.get("benchmark", []), start=1):
            bench_uri = f"#{res['test_id']}_benchmark_{idx}"
            bench = {
                "@id": bench_uri,
                "@type": "ftr:Benchmark",
                "dcterms:identifier": str(val),
                "dcterms:title": str(val),
                "dcterms:description": f"Allowed value: {val}",
            }
            graph.append(bench)
            test_node["ftr:hasBenchmark"].append(bench_uri)

        result_uri = f"#{res['test_id']}_result"
        result_node = {
            "@id": result_uri,
            "@type": "ftr:TestResult",
            "ftr:outputFromTest": test_uri,
            "dcterms:identifier": res["test_id"],
            "dcterms:title": f"Result for {res['metric_id']}",
            "dcterms:description": res["comment"],
            "prov:value": res["status"],
            "ftr:status": res["status"],
            "ftr:completion": "100",
            "ftr:log": res["comment"],
        }
        graph.append(result_node)
        result_set["prov:hadMember"].append(result_uri)

    out = {"@context": "https://w3id.org/ftr/context.jsonld"}
    for node in graph:
        node_id = node.get("@id")
        if node_id:
            out[node_id] = node

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{dmp_id}_ostrails_results.jsonld")
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)

    return output_path
