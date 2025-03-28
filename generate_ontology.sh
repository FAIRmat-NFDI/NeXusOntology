#!/bin/bash

# Add NeXusOntology to PYTHONPATH
export PYTHONPATH=/home/nomad/work/NeXusOntology:$PYTHONPATH

python -m script.generate_ontology
python -m script.generate_ontology full
