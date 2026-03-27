"""Ontology browsing endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel
import os
import httpx

router = APIRouter()

# Configuration from environment
FUSEKI_URL = os.environ.get("FUSEKI_URL", "http://fuseki:3030")
FUSEKI_DATASET = os.environ.get("FUSEKI_DATASET", "kgbuilder")


class OntologyAttribute(BaseModel):
    id: str
    name: str
    dataType: str
    required: bool
    description: str = ""
    sourceDataType: str = ""
    cardinality: str = "0..1"
    exampleValue: str | None = None


class OntologyClass(BaseModel):
    id: str
    name: str
    module: str = "Core"
    description: str = ""
    parentClassId: str | None = None
    exampleInstanceId: str | None = None
    attributes: list[OntologyAttribute] = []


class OntologyRelation(BaseModel):
    id: str
    name: str
    domainClassId: str | None = None
    rangeClassId: str | None = None
    description: str = ""
    inverseName: str = ""
    cardinality: str = "0..n"
    exampleTriple: str | None = None


class OntologySummary(BaseModel):
    id: str
    name: str
    version: str
    classes: list[OntologyClass]
    relations: list[OntologyRelation]


async def _query_fuseki(sparql: str) -> list[dict[str, str]]:
    """Execute SPARQL query against Fuseki."""
    prefixes = """\
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    """

    if not sparql.strip().upper().startswith("PREFIX"):
        sparql = prefixes + "\n" + sparql

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{FUSEKI_URL}/{FUSEKI_DATASET}/sparql",
                data={"query": sparql},
                headers={"Accept": "application/sparql-results+json"},
            )
            resp.raise_for_status()
            data = resp.json()
            bindings = data.get("results", {}).get("bindings", [])
            return [
                {k: v.get("value", "") for k, v in binding.items()}
                for binding in bindings
            ]
    except Exception as e:
        print(f"SPARQL query failed: {e}")
        return []


@router.get("/summary", response_model=OntologySummary)
async def get_ontology_summary() -> OntologySummary:
    """Get full ontology summary (classes, relations, hierarchy)."""
    # Fetch classes with attributes
    classes_sparql = """
SELECT DISTINCT ?class ?label ?description ?parent
WHERE {
    ?class a owl:Class .
    OPTIONAL { ?class rdfs:label ?label . }
    OPTIONAL { ?class rdfs:comment ?description . }
    OPTIONAL { ?class rdfs:subClassOf ?parent . FILTER(?parent != owl:Thing) }
}
ORDER BY ?label
    """

    class_results = await _query_fuseki(classes_sparql)
    classes = {}

    for row in class_results:
        class_uri = row.get("class", "")
        if not class_uri:
            continue

        local_name = class_uri.split("#")[-1].split("/")[-1]
        parent_uri = row.get("parent", "")
        parent_id = parent_uri.split("#")[-1] if parent_uri else None

        cls_id = f"cls:{local_name}"
        classes[cls_id] = OntologyClass(
            id=cls_id,
            name=local_name,
            description=row.get("description", ""),
            parentClassId=f"cls:{parent_id}" if parent_id else None,
            attributes=[],
        )

        # Fetch attributes for this class
        attr_sparql = f"""
SELECT ?prop ?propLabel ?description ?range
WHERE {{
    ?prop a owl:DatatypeProperty .
    ?prop rdfs:domain <{class_uri}> .
    OPTIONAL {{ ?prop rdfs:label ?propLabel . }}
    OPTIONAL {{ ?prop rdfs:comment ?description . }}
    OPTIONAL {{ ?prop rdfs:range ?range . }}
}}
        """
        attr_results = await _query_fuseki(attr_sparql)

        for attr_row in attr_results:
            prop_uri = attr_row.get("prop", "")
            if not prop_uri:
                continue

            prop_local = prop_uri.split("#")[-1].split("/")[-1]
            range_uri = attr_row.get("range", "xsd:string")

            classes[cls_id].attributes.append(
                OntologyAttribute(
                    id=f"attr:{prop_local}",
                    name=prop_local,
                    dataType="string",
                    required=False,
                    description=attr_row.get("description", ""),
                    sourceDataType=range_uri,
                    cardinality="0..1",
                )
            )

    # Fetch relations
    relations_sparql = """
SELECT ?prop ?label ?description ?domain ?range
WHERE {
    ?prop a owl:ObjectProperty .
    OPTIONAL { ?prop rdfs:label ?label . }
    OPTIONAL { ?prop rdfs:comment ?description . }
    OPTIONAL { ?prop rdfs:domain ?domain . }
    OPTIONAL { ?prop rdfs:range ?range . }
}
ORDER BY ?label
    """

    rel_results = await _query_fuseki(relations_sparql)
    relations = []

    for row in rel_results:
        prop_uri = row.get("prop", "")
        if not prop_uri:
            continue

        prop_local = prop_uri.split("#")[-1].split("/")[-1]
        domain_uri = row.get("domain", "")
        range_uri = row.get("range", "")

        domain_id = f"cls:{domain_uri.split('#')[-1]}" if domain_uri else None
        range_id = f"cls:{range_uri.split('#')[-1]}" if range_uri else None

        relations.append(
            OntologyRelation(
                id=f"rel:{prop_local}",
                name=prop_local,
                domainClassId=domain_id,
                rangeClassId=range_id,
                description=row.get("description", ""),
            )
        )

    return OntologySummary(
        id="ontology-kgplatform",
        name="KGPlatform Ontology",
        version="1.0.0",
        classes=list(classes.values()),
        relations=relations,
    )


@router.get("/classes", response_model=list[OntologyClass])
async def get_classes() -> list[OntologyClass]:
    """List all ontology classes."""
    summary = await get_ontology_summary()
    return summary.classes


@router.get("/relations", response_model=list[OntologyRelation])
async def get_relations() -> list[OntologyRelation]:
    """List all ontology relations."""
    summary = await get_ontology_summary()
    return summary.relations
