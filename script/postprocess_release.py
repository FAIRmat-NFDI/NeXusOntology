#!/usr/bin/env python3
"""Post-process a generated NeXusOntology OWL file for release.

Two jobs:

1. Stamp release-level metadata onto the owl:Ontology node (owl:versionIRI,
   owl:versionInfo, dcterms:issued, owl:priorVersion, rdfs:seeAlso to the
   GitHub release).

2. Make the manual.nexusformat.org links visible in the Widoco documentation.
   The generator writes them as rdfs:seeAlso *string literals*.  Widoco's LODE
   parser ignores rdfs:seeAlso entirely, so those links never appear in the
   HTML.  We therefore (a) retype them as IRI resources, which is the correct
   RDF anyway, and (b) mirror them onto rdfs:isDefinedBy, which Widoco *does*
   render, as a clickable link.

Finally, write the ttl / nt / jsonld serializations that the w3id content
negotiation rules point at.
"""

import argparse
import datetime
import pathlib
import sys

from rdflib import Graph, Literal, URIRef, XSD
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS

BASE = URIRef("https://w3id.org/PaN/NeXus/definitions")

SERIALIZATIONS = {
    "ttl": "turtle",
    "nt": "nt",
    "jsonld": "json-ld",
}


def link_annotations(g: Graph) -> tuple[int, int]:
    """Retype seeAlso literals as IRIs and mirror them onto isDefinedBy."""
    retyped = mirrored = 0
    for subject, obj in list(g.subject_objects(RDFS.seeAlso)):
        if not isinstance(obj, Literal):
            target = obj
        else:
            text = str(obj).strip()
            if not text.startswith(("http://", "https://")):
                continue  # not a URL; leave the literal alone
            target = URIRef(text)
            g.remove((subject, RDFS.seeAlso, obj))
            g.add((subject, RDFS.seeAlso, target))
            retyped += 1
        if (subject, RDFS.isDefinedBy, target) not in g:
            g.add((subject, RDFS.isDefinedBy, target))
            mirrored += 1
    return retyped, mirrored


def stamp_version(g: Graph, version: str, defs_tag: str, defs_sha: str,
                  prior: str | None, release_url: str | None) -> None:
    version_iri = URIRef(f"{BASE}/{version}")
    g.add((BASE, RDF.type, OWL.Ontology))
    g.set((BASE, OWL.versionIRI, version_iri))
    g.set((BASE, OWL.versionInfo, Literal(version)))
    g.set((BASE, DCTERMS.issued,
           Literal(datetime.date.today().isoformat(), datatype=XSD.date)))
    g.add((BASE, DCTERMS.hasVersion, Literal(version)))
    g.add((BASE, DCTERMS.source, URIRef(
        f"https://github.com/nexusformat/definitions/tree/{defs_sha}")))
    g.add((BASE, RDFS.comment, Literal(
        f"Generated from nexusformat/definitions {defs_tag} ({defs_sha[:7]}).")))
    if prior:
        g.set((BASE, OWL.priorVersion, URIRef(f"{BASE}/{prior}")))
    if release_url:
        g.add((BASE, RDFS.seeAlso, URIRef(release_url)))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="infile", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--basename", required=True,
                    help="e.g. NeXusOntology_full")
    ap.add_argument("--version", required=True, help="e.g. v2026.01")
    ap.add_argument("--definitions-tag", required=True)
    ap.add_argument("--definitions-sha", required=True)
    ap.add_argument("--prior-version", default=None)
    ap.add_argument("--release-url", default=None)
    ap.add_argument("--serializations", default="ttl,nt,jsonld")
    args = ap.parse_args()

    outdir = pathlib.Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    g = Graph()
    g.parse(args.infile, format="xml")
    print(f"parsed {len(g)} triples from {args.infile}")

    retyped, mirrored = link_annotations(g)
    print(f"seeAlso literals retyped as IRIs: {retyped}")
    print(f"isDefinedBy annotations added:    {mirrored}")

    stamp_version(g, args.version, args.definitions_tag, args.definitions_sha,
                  args.prior_version, args.release_url)

    owl_path = outdir / f"{args.basename}.owl"
    g.serialize(destination=owl_path, format="xml")
    print(f"wrote {owl_path}")

    for ext in [s.strip() for s in args.serializations.split(",") if s.strip()]:
        if ext not in SERIALIZATIONS:
            print(f"unknown serialization {ext!r}, skipping", file=sys.stderr)
            continue
        path = outdir / f"{args.basename}.{ext}"
        g.serialize(destination=path, format=SERIALIZATIONS[ext])
        print(f"wrote {path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())