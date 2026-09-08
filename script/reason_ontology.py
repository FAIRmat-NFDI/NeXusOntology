#!/usr/bin/env python3
"""Run a reasoner over the ontology and save the materialized result."""

import argparse
import sys

import owlready2


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="infile", required=True)
    ap.add_argument("--out", dest="outfile", required=True)
    args = ap.parse_args()

    onto = owlready2.get_ontology(f"file://{args.infile}").load()
    print(f"loaded {len(list(onto.classes()))} classes")

    with onto:
        owlready2.sync_reasoner_hermit(infer_property_values=True)

    onto.save(file=args.outfile, format="rdfxml")
    print(f"wrote {args.outfile}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
