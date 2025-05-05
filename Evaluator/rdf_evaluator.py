from rdflib import Graph

def sparql_completeness_check(rdf_path):
    g = Graph()
    g.parse(rdf_path, format='turtle')

    query = """
    ASK WHERE {
        ?dmp a <http://example.org/dmp#DataManagementPlan> ;
             <http://example.org/dmp#hasContact> ?contact .
        ?contact <http://example.org/dmp#name> ?name .
    }
    """

    result = g.query(query)
    completeness = bool(result.askAnswer)
    print(f"✅ Completeness Check Passed? {completeness}")
    return completeness

if __name__ == "__main__":
    sparql_completeness_check("C:/Users/berni/OneDrive - TU Wien/THESIS/Code/DMP-Evaluation/examples/ex9-dmp-long.ttl")