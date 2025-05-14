import json
from rdflib import Graph, Namespace, Literal, RDF, URIRef
from urllib.parse import quote  

DMP = Namespace("http://example.org/dmp#")

def json_to_rdf(json_path, rdf_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    dmp = data.get("dmp", {})
    g = Graph()
    g.bind("dmp", DMP)

    # Basic metadata conversion example:
    dmp_uri = URIRef(dmp["dmp_id"]["identifier"])
    g.add((dmp_uri, RDF.type, DMP.DataManagementPlan))
    g.add((dmp_uri, DMP.title, Literal(dmp["title"])))
    g.add((dmp_uri, DMP.description, Literal(dmp["description"])))

    # Contact
    contact_uri = URIRef(dmp["contact"]["contact_id"]["identifier"])
    g.add((contact_uri, RDF.type, DMP.Contact))
    g.add((contact_uri, DMP.name, Literal(dmp["contact"]["name"])))
    g.add((dmp_uri, DMP.hasContact, contact_uri))

    # Dataset and Distribution info (with URI encoding clearly fixed)
    for ds in dmp.get("dataset", []):
        ds_uri = URIRef(ds["dataset_id"]["identifier"])
        g.add((ds_uri, RDF.type, DMP.Dataset))
        g.add((ds_uri, DMP.title, Literal(ds["title"])))
        g.add((dmp_uri, DMP.hasDataset, ds_uri))

        for dist in ds.get("distribution", []):
            host_info = dist.get("host", {})
            host_url = host_info.get("url")
            if host_url:
                dist_uri = URIRef(host_url)
            else:
                # Now safely URL-encode clearly:
                title_encoded = quote(dist.get('title', 'unknown'))
                dist_uri = URIRef(f"{ds_uri}/distribution/{title_encoded}")

            g.add((dist_uri, RDF.type, DMP.Distribution))
            g.add((dist_uri, DMP.dataAccess, Literal(dist.get("data_access", "unknown"))))
            g.add((ds_uri, DMP.hasDistribution, dist_uri))

            licenses = dist.get("license", [])
            for lic in licenses:
                license_ref = lic.get("license_ref")
                if license_ref:
                    g.add((dist_uri, DMP.license, URIRef(license_ref)))

    # Save RDF as Turtle (.ttl)
    g.serialize(destination=rdf_path, format='turtle')
    print(f" RDF saved successfully at {rdf_path}")

if __name__ == "__main__":
    json_to_rdf(
        "C:/Users/berni/OneDrive - TU Wien/THESIS/Code/DMP-Evaluation/examples/ex9-dmp-long.json",
        "C:/Users/berni/OneDrive - TU Wien/THESIS/Code/DMP-Evaluation/examples/ex9-dmp-long.ttl"
    )
