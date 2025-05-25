import owlready2
from .NeXusOntology import NeXusOntology
import pygit2
import os
import sys

def main(full=False, nexus_def_path=None, def_commit=None):
    print(f"Debug: Generating ontology with full={full}")
    local_dir = os.path.abspath(os.path.dirname(__file__))
    os.environ['NEXUS_DEF_PATH'] = nexus_def_path

    # Official NeXus definitions: https://manual.nexusformat.org/classes/
    web_page_base_prefix = 'https://manual.nexusformat.org/'

    detailed_iri = 'http://purl.org/nexusformat/v2.0/definitions/' + def_commit + '/'
    base_iri = 'http://purl.org/nexusformat/definitions/'
    onto = owlready2.get_ontology(base_iri + "NeXusOntology")

    nexus_ontology = NeXusOntology(onto, base_iri, web_page_base_prefix, def_commit, full)
    nexus_ontology.gen_classes()
    nexus_ontology.gen_children()
    if full:
        nexus_ontology.gen_datasets()
        fullsuffix = '_full'
    else:
        fullsuffix = ''
    
    # Include the commit hash in the output file name
    output_file_name = f"NeXusOntology{fullsuffix}_{def_commit}.owl"
    output_path = os.path.join(local_dir, f"..{os.sep}ontology{os.sep}{output_file_name}")
    onto.save(file=output_path, format="rdfxml")

if __name__ == "__main__":
    import sys
    local_dir = os.path.abspath(os.path.dirname(__file__))
    one_up = os.path.join(local_dir, "..", "definitions")
    two_up = os.path.join(local_dir, "..", "..", "definitions")
    if os.path.isdir(one_up):
        nexus_def_path = one_up
    elif os.path.isdir(two_up):
        nexus_def_path = two_up
    else:
        raise FileNotFoundError("definitions folder not found one or two directories up from script location.")
    full = len(sys.argv) > 1 and sys.argv[1] == 'full'
    repo = pygit2.Repository(nexus_def_path)
    # Check for provided commit hash argument
    if len(sys.argv) > 2:
        commit_hash = sys.argv[2]
        try:
            # Use the provided commit hash directly
            commit = repo.revparse_single(commit_hash)
            repo.checkout_tree(commit)
            repo.set_head(commit.id)  # Update HEAD to point to the commit
            def_commit = commit_hash[:7]  # Use the provided commit hash
            print(f"Checked out commit hash: {commit_hash} (commit: {def_commit})")
        except KeyError:
            print(f"Error: Commit hash '{commit_hash}' not found in the repository.")
            sys.exit(1)
    else:
        # Use the current HEAD commit if no version is specified
        def_commit = str(repo.head.target)[:7]
    main(full=full, nexus_def_path=nexus_def_path, def_commit=def_commit)