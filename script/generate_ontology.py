import owlready2
from .NeXusOntology import NeXusOntology
import pygit2
import os
import sys

local_dir = os.path.abspath(os.path.dirname(__file__))
nexus_def_path = os.path.join(local_dir, f"..{os.sep}definitions")
os.environ['NEXUS_DEF_PATH']=nexus_def_path

repo = pygit2.Repository(nexus_def_path)
def_commit = repo.head.target.hex[:7]

# Official NeXus definitions: https://manual.nexusformat.org/classes/
web_page_base_prefix = 'https://manual.nexusformat.org/'

detailed_iri = 'http://purl.org/nexusformat/v2.0/definitions/' + def_commit + '/'
base_iri = 'http://purl.org/nexusformat/definitions/'
onto = owlready2.get_ontology(base_iri + "NeXusOntology")


full = len(sys.argv)>1 and sys.argv[1] == 'full'

nexus_ontology = NeXusOntology(onto, base_iri, web_page_base_prefix, def_commit, full)
nexus_ontology.gen_classes()
nexus_ontology.gen_children()
if full:
  nexus_ontology.gen_datasets()
  fullsuffix='_full'
else:
  fullsuffix=''

onto.save(file = os.path.join(local_dir, f"..{os.sep}ontology{os.sep}NeXusOntology{fullsuffix}.owl"), format = "rdfxml")

