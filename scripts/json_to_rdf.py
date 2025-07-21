import json
from rdflib import Graph, Namespace, Literal, RDF, URIRef
from urllib.parse import quote

DMP = Namespace("http://example.org/dmp#")

def json_to_rdf(json_path, rdf_path):
    """Convert a maDMP JSON file to a Turtle representation."""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    dmp = data.get("dmp", {})
    g = Graph()
    g.bind("dmp", DMP)

    # Metadata conversion example:
    dmp_uri = URIRef(dmp["dmp_id"]["identifier"])
    g.add((dmp_uri, RDF.type, DMP.DataManagementPlan))
    g.add((dmp_uri, DMP.title, Literal(dmp["title"])))
    g.add((dmp_uri, DMP.description, Literal(dmp["description"])))

    # Contact
    contact_uri = URIRef(dmp["contact"]["contact_id"]["identifier"])
    g.add((contact_uri, RDF.type, DMP.Contact))
    g.add((contact_uri, DMP.name, Literal(dmp["contact"]["name"])))
    g.add((dmp_uri, DMP.hasContact, contact_uri))

    # Dataset and Distribution info
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
                # URL-encode:
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
    print(f"RDF saved successfully at {rdf_path}")

def jsonld_to_triples(jsonld_path, ttl_path):
    """Parse a JSON-LD document and store it as Turtle."""

    g = Graph()
    with open(jsonld_path, 'r', encoding='utf-8') as fh:
        data = json.load(fh)

    g.parse(data=json.dumps(data), format='json-ld')

    g.serialize(destination=ttl_path, format='turtle')
    print(f"Converted {jsonld_path} to {ttl_path}")

if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(
        description="Convert a maDMP JSON or JSON-LD file to RDF formats"
    )
    parser.add_argument(
        "input",
        help="Path to the input JSON or JSON-LD file",
    )
    parser.add_argument(
        "output_dir",
        help="Directory to store the converted .ttl file",
    )
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    base = os.path.splitext(os.path.basename(args.input))[0]
    ttl_path = os.path.join(args.output_dir, base + ".ttl")

    if args.input.endswith(".jsonld"):
        jsonld_to_triples(args.input, ttl_path)
    else:
        json_to_rdf(args.input, ttl_path)