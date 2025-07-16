import argparse
import json
import os
import re
from urllib.parse import urldefrag

import requests
from rdflib import ConjunctiveGraph, URIRef
from rdflib.namespace import RDF, RDFS, DC, Namespace

# Map FIP question URIs to FAIR principle, maDMP field and question text
QUESTION_MAP = {
    "https://w3id.org/fair/fip/terms/FIP-Question-F1-MD": {
        "principle": "F1",
        "madmp": "dataset.dataset_id.identifier",
        "text": "What globally unique, persistent, resolvable identifiers do you use for metadata records?",
    },
    "https://w3id.org/fair/fip/terms/FIP-Question-F1-D": {
        "principle": "F1",
        "madmp": "dataset.dataset_id.identifier",
        "text": "What globally unique, persistent, resolvable identifiers do you use for datasets?",
    },
    "https://w3id.org/fair/fip/terms/FIP-Question-F2": {
        "principle": "F2",
        "madmp": "dataset.metadata.metadata_standard_id.identifier",
        "text": "Which metadata schemas do you use for findability?",
    },
    "https://w3id.org/fair/fip/terms/FIP-Question-F3": {
        "principle": "F3",
        "madmp": "dataset.distribution.host.pid_system",
        "text": "What is the technology that links the persistent identifiers of your data to the metadata description?",
    },
    "https://w3id.org/fair/fip/terms/FIP-Question-F4-MD": {
        "principle": "F4",
        "madmp": "dataset.distribution.access_url",
        "text": "In which search engines are your metadata records indexed?",
    },
    "https://w3id.org/fair/fip/terms/FIP-Question-F4-D": {
        "principle": "F4",
        "madmp": "dataset.distribution.access_url",
        "text": "In which search engines are your datasets indexed?",
    },
    "https://w3id.org/fair/fip/terms/FIP-Question-A1.1-MD": {
        "principle": "A1.1",
        "madmp": "dataset.distribution.host.url",
        "text": "Which standardized communication protocol do you use for metadata records?",
    },
    "https://w3id.org/fair/fip/terms/FIP-Question-A1.1-D": {
        "principle": "A1.1",
        "madmp": "dataset.distribution.host.url",
        "text": "Which standardized communication protocol do you use for datasets?",
    },
    "https://w3id.org/fair/fip/terms/FIP-Question-A1.2-MD": {
        "principle": "A1.2",
        "madmp": "dataset.distribution.data_access",
        "text": "Which authentication & authorisation technique do you use for metadata records?",
    },
    "https://w3id.org/fair/fip/terms/FIP-Question-A1.2-D": {
        "principle": "A1.2",
        "madmp": "dataset.distribution.data_access",
        "text": "Which authentication & authorisation technique do you use for datasets?",
    },
    "https://w3id.org/fair/fip/terms/FIP-Question-A2": {
        "principle": "A2",
        "madmp": "",
        "text": "Which metadata longevity plan do you use?",
    },
    "https://w3id.org/fair/fip/terms/FIP-Question-I1-MD": {
        "principle": "I1",
        "madmp": "",
        "text": "Which knowledge representation languages (allowing machine interoperation) do you use for metadata records?",
    },
    "https://w3id.org/fair/fip/terms/FIP-Question-I1-D": {
        "principle": "I1",
        "madmp": "",
        "text": "Which knowledge representation languages (allowing machine interoperation) do you use for datasets?",
    },
    "https://w3id.org/fair/fip/terms/FIP-Question-I2-MD": {
        "principle": "I2",
        "madmp": "dataset.metadata.metadata_standard_id.identifier",
        "text": "Which structured vocabularies do you use to annotate your metadata records?",
    },
    "https://w3id.org/fair/fip/terms/FIP-Question-I2-D": {
        "principle": "I2",
        "madmp": "dataset.metadata.metadata_standard_id.identifier",
        "text": "Which structured vocabularies do you use to encode your datasets?",
    },
    "https://w3id.org/fair/fip/terms/FIP-Question-I3-MD": {
        "principle": "I3",
        "madmp": "dataset.metadata.metadata_standard_id.type",
        "text": "Which models, schema(s) do you use for your metadata records?",
    },
    "https://w3id.org/fair/fip/terms/FIP-Question-I3-D": {
        "principle": "I3",
        "madmp": "dataset.metadata.metadata_standard_id.type",
        "text": "Which models, schema(s) do you use for your datasets?",
    },
    "https://w3id.org/fair/fip/terms/FIP-Question-R1.1-MD": {
        "principle": "R1.1",
        "madmp": "dataset.distribution.license.license_ref",
        "text": "Which usage license do you use for your metadata records?",
    },
    "https://w3id.org/fair/fip/terms/FIP-Question-R1.1-D": {
        "principle": "R1.1",
        "madmp": "dataset.distribution.license.license_ref",
        "text": "Which usage license do you use for your datasets?",
    },
    "https://w3id.org/fair/fip/terms/FIP-Question-R1.2-MD": {
        "principle": "R1.2",
        "madmp": "dataset.data_quality_assurance",
        "text": "Which metadata schemas do you use for describing the provenance of your metadata records?",
    },
    "https://w3id.org/fair/fip/terms/FIP-Question-R1.2-D": {
        "principle": "R1.2",
        "madmp": "dataset.data_quality_assurance",
        "text": "Which metadata schemas do you use for describing the provenance of your datasets?",
    },
}

FIP_DECLARATION = URIRef("https://w3id.org/fair/fip/terms/FIP-Declaration")
FIP_NO_CHOICE = URIRef("https://w3id.org/fair/fip/terms/FIP-No-Choice-Declaration")
HAS_INDEX = URIRef("https://w3id.org/fair/fip/terms/has-declaration-index")
INCLUDES = URIRef("http://purl.org/nanopub/x/includesElement")
REFERS_TO = URIRef("https://w3id.org/fair/fip/terms/refers-to-question")
CURRENT_USE = URIRef("https://w3id.org/fair/fip/terms/declares-current-use-of")
PLANNED_USE = URIRef("https://w3id.org/fair/fip/terms/declares-planned-use-of")
CONSIDERATIONS = URIRef("https://w3id.org/fair/fip/terms/considerations")
SCHEMA = Namespace("https://schema.org/")


def fetch_graph(uri: str) -> ConjunctiveGraph:
    resp = requests.get(uri, headers={"Accept": "application/trig"})
    resp.raise_for_status()
    g = ConjunctiveGraph()
    g.parse(data=resp.text, format="trig")
    return g


def get_label(uri: str) -> str:
    base, frag = urldefrag(uri)
    g = fetch_graph(base)
    label = g.value(URIRef(uri), RDFS.label)
    if label:
        label = str(label)
        if "|" in label:
            label = label.split("|")[0]
        return label
    return ""

def get_fip_label(uri: str) -> str:
    g = fetch_graph(uri)
    fip_type = URIRef("https://w3id.org/fair/fip/terms/FAIR-Implementation-Profile")
    for subj in g.subjects(RDF.type, fip_type):
        label = g.value(subj, RDFS.label) or g.value(subj, DC.title)
        if label:
            text = str(label)
            return re.sub(r"[^\w.-]", "_", text.strip())
    return "unknown"


def process_declaration(uri: str):
    g = fetch_graph(uri)
    subj = g.value(predicate=REFERS_TO)
    if subj is None:
        # try any subject with property
        for s in g.subjects(REFERS_TO):
            subj = s
            break
    question_uri = str(g.value(subj, REFERS_TO))
    info = QUESTION_MAP.get(question_uri, {})
    allowed = []
    for p in (CURRENT_USE, PLANNED_USE):
        for val in g.objects(subj, p):
            allowed.append(get_label(str(val)))
    comment = g.value(subj, CONSIDERATIONS)
    version = g.value(subj, SCHEMA.version)
    return {
        "Question_URI": question_uri,
        "FAIR_principle": info.get("principle", ""),
        "FIP_question": info.get("text", question_uri),
        "maDMP_field": info.get("madmp", ""),
        "Mapping_status": "Mapped" if info.get("madmp") else None,
        "Comments": str(comment) if comment else "",
        "Allowed_values": [v for v in allowed if v],
        "Metric_version": str(version) if version else "",
    }


def build_mapping(main_uri: str):
    g = fetch_graph(main_uri)
    index_node = next(g.objects(None, HAS_INDEX), None)
    if not index_node:
        raise ValueError("Declaration index not found in main nanopub")
    index_uri = str(index_node)
    idx_graph = fetch_graph(index_uri)
    declarations = [str(u) for u in idx_graph.objects(None, INCLUDES)]
    mapping_dict = {}
    for d in declarations:
        result = process_declaration(d)
        mapping_dict[result["Question_URI"]] = result

    ordered = []
    for q_uri in QUESTION_MAP.keys():
        if q_uri in mapping_dict:
            ordered.append(mapping_dict.pop(q_uri))

    # append any remaining entries not in QUESTION_MAP
    ordered.extend(mapping_dict.values())
    return {"FIP_maDMP_Mapping": ordered}


def main():
    parser = argparse.ArgumentParser(description="Generate FIP-maDMP mapping from a FIP nanopublication")
    parser.add_argument("uri", help="URI of the FIP nanopublication")
    parser.add_argument("--output", "-o", default="FIP_Mapping", help="Output directory")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)
    mapping = build_mapping(args.uri)

    label = get_fip_label(args.uri)
    name = f"fip_madmp_{label}.json"
    path = os.path.join(args.output, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2)
    print(f"Mapping saved to: {path}")


if __name__ == "__main__":
    main()