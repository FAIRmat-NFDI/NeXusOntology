import owlready2
from .NeXusOntology import NeXusOntology
import pygit2
import os
import sys

def main(full=False, testdata = False, nexus_def_path=None, def_commit=None, store_commit_filename = False, imports=[]):
    print(f"Debug: Generating ontology with full={full} and testdata={testdata}")
    local_dir = os.path.abspath(os.path.dirname(__file__))
    os.environ['NEXUS_DEF_PATH'] = nexus_def_path

    # Official NeXus definitions: https://manual.nexusformat.org/classes/
    web_page_base_prefix = 'https://manual.nexusformat.org/'

    base_iri = 'https://w3id.org/nexusformat/definitions'
    onto = owlready2.get_ontology(base_iri)

    if imports:
        for import_iri in imports:
            onto.imported_ontologies.append(owlready2.get_ontology(import_iri))

    nexus_ontology = NeXusOntology(onto, base_iri, web_page_base_prefix, def_commit, full)
    nexus_ontology.gen_classes()
    nexus_ontology.gen_children()
    if full:
        if testdata:
            nexus_ontology.gen_datasets()
            fullsuffix = '_full_testdata'
        else:
            fullsuffix = '_full'
    else:
        fullsuffix = ''
    
    # Include the commit hash in the output file name

    def_commit_text = f"_{def_commit}" if store_commit_filename else "" 
    output_file_name = f"NeXusOntology{fullsuffix}{def_commit_text}.owl"
    output_path = os.path.join(local_dir, f"..{os.sep}ontology{os.sep}{output_file_name}")
    onto.save(file=output_path, format="rdfxml")

if __name__ == "__main__":
    import sys
    local_dir = os.path.abspath(os.path.dirname(__file__))
    one_up = os.path.join(local_dir, "..", "definitions")
    two_up = os.path.join(local_dir, "..", "..", "definitions")
    if os.path.isdir(two_up):
        nexus_def_path = two_up
    elif os.path.isdir(one_up):
        nexus_def_path = one_up
    else:
        raise FileNotFoundError("definitions folder not found one or two directories up from script location.")
    commit_arg = 1
    full = len(sys.argv) > 1 and sys.argv[1] == "full"
    if full:
        commit_arg = 2
    testdata = full and len(sys.argv) > 2 and sys.argv[2] == "testdata"
    if testdata:
        commit_arg = 3
    store_commit_filename = (
        (testdata and len(sys.argv) > 3 and sys.argv[3] == "store_commit_filename") or
        (full and not testdata and len(sys.argv) > 2 and sys.argv[2] == "store_commit_filename") or
        (not full and len(sys.argv) > 1 and sys.argv[1] == "store_commit_filename")
    )
    repo = pygit2.Repository(nexus_def_path)
    # Check for provided commit hash argument
    if len(sys.argv) > commit_arg:
        commit_hash = sys.argv[commit_arg]
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

    main(full=full, testdata=testdata, nexus_def_path=nexus_def_path, def_commit=def_commit, store_commit_filename=store_commit_filename)