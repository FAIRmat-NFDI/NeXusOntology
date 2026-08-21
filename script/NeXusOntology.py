from os import walk
import owlready2
import types
import hashlib
import re

from . import nxdl


script_files = next(walk("./"), (None, None, []))[2]
script_files = sorted(filter(lambda filename: filename.endswith(".py"), script_files))

_NON_ALNUM = re.compile(r"[^a-z0-9]+")

def _slugify(text):
    """Turn arbitrary text (e.g. an nxdl enumeration item's value) into a
    safe IRI local-name segment, collapsing any run of non-alphanumeric
    characters into a single hyphen. This is deliberately aggressive
    (Widoco's own namespace-declaration table renders incorrectly for
    *any* leftover punctuation, not just brackets/quotes) - collisions
    this causes between distinct values (e.g. NXdispersion_table's
    "n + ik" vs "n - ik", which would otherwise both collapse to
    "n-ik") are handled by __unique_enum_slug's disambiguation, not here."""
    slug = _NON_ALNUM.sub("-", text.lower()).strip("-")
    return slug or "empty"

def get_script_hash():
    h = hashlib.sha1()
    for file in script_files:
        with open(file, "rb") as f:
            h.update(f.read())
    return h.hexdigest()

class NeXusOntology:

    def __init__(self, onto, base_iri, web_page_base_prefix, versionInfo, full = True):
        self.__onto__ = onto
        self.enums = {}
        self.__used_enum_slugs__ = set()
        self.nxdl_info = nxdl.load_all_nxdls(full)
        self.base_iri = base_iri
        self.web_page_base_prefix = web_page_base_prefix
        self.web_page_prefix = self.web_page_base_prefix + "classes/"
        self.versionInfo = versionInfo
        self.setup_owl_parents()
        self.setup_ontology_metadata()
        self.data_types = self.get_data_types()
        self.unit_categories = self.get_unit_categories()

    def setup_ontology_metadata(self):
        onto = self.__onto__

        with onto:
            class abstract(owlready2.AnnotationProperty):
                pass
            abstract.iri = "http://purl.org/dc/terms/abstract"

            class description(owlready2.AnnotationProperty):
                pass
            description.iri = "http://purl.org/dc/terms/description"

            class introduction(owlready2.AnnotationProperty):
                pass
            introduction.iri = "https://w3id.org/widoco/vocab#introduction"

            onto.metadata.abstract.append(
                owlready2.locstr(
                    "The NeXus Ontology is a formal semantic representation of the NeXus data standard," +
                    "providing a structured vocabulary for experimental materials science, neutron, X-ray, " +
                    "and muon facilities. By translating the hierarchical NeXus Application Definitions (NXDL) " + 
                    "into the Web Ontology Language (OWL), this ontology facilitates FAIR data principles. " +
                    "It enables machine-actionability, automated data indexing, and advanced semantic reasoning " +
                    "across diverse scientific data management pipelines.", 
                    lang="en"
                )
            )

            onto.metadata.description.append(
                owlready2.locstr(
                    "The NeXus Ontology maps the structural components of the NeXus hierarchical format—including " +
                    "base classes, application definitions, fields, and dimensions into a comprehensive semantic graph. " +
                    "This mapping transforms raw experimental data schemas into a standardized ontology that supports " +
                    "automated inference and integration with external knowledge graphs. " + 
                    "Designed for seamless integration into modern research data management platforms, " +
                    "the ontology provides the semantic scaffolding necessary to parse complex measurement workflows. " +
                    "By defining explicit relationships between instruments, physical properties, " +
                    "and measurement protocols, it supports the extraction and standardization of metadata. " +
                    " The ontology is persistently resolvable via the w3id.org namespace, ensuring stable, " +
                    "long-term integration for standalone ontology services, automated REST endpoints, and customized " +
                    "data extraction plugins tailored to advanced solid-state physics and materials characterization.", 
                    lang="en"
                )
            )

            onto.metadata.introduction.append(
                owlready2.locstr(
                    "Welcome to the documentation for the NeXus Ontology. This framework serves as a critical bridge " +
                    "between the established NeXus data format and the Semantic Web, bringing robust knowledge " +
                    "representation to experimental physics and materials science. " +
                    "In this documentation, you will find a complete taxonomy of the NeXus classes, object properties, " +
                    "and data properties. Navigating through the sections will reveal how instrument components and" +
                    "experimental measurements are logically structured. Whether you are validating measurement protocol configurations, "+
                    "developing automated indexing services, or mapping laboratory data to FAIR standards, "+
                    "this ontology provides the necessary semantic infrastructure to ensure your datasets are interoperable and fully machine-readable. ", 
                    lang="en"
                )
            )

    def setup_owl_parents(self):
        with self.__onto__:
            class NeXus(owlready2.Thing):
                comment = 'NeXus concept'
                versionInfo = self.versionInfo
            self.NeXus = NeXus
 
            class NeXusObject(NeXus):
                # comment = self.nxdl_info["base_classes"]['NXobject']['doc'].replace('\t','') # NeXus documentation string 
                comment = 'NeXus Object (All the concepts defined by the NeXus definitions)'
                # seeAlso = base_class_web_page_prefix + 'NXobject' + '.html'
                # iri = self.base_iri + 'NXobject'   #set iri using agree pattern for Nexus
            self.NeXusObject = NeXusObject

            class NeXusBaseClass(NeXusObject):
                comment = 'NeXus Base Class (Newer entries are found in Contributed Definitions)'
                seeAlso = self.web_page_prefix + 'base_classes/index.html'
            self.NeXusBaseClass = NeXusBaseClass

            class NeXusApplicationClass(NeXusObject):
                comment = 'NeXus Application Class (Newer entries are found in Contributed Definitions)'
                seeAlso = self.web_page_prefix + 'applications/index.html'
            self.NeXusApplicationClass = NeXusApplicationClass

            class NeXusQuantity(NeXusObject):
                comment = 'NeXus Quantity (Attributes and Fields which can contain actual data values)'
            self.NeXusQuantity = NeXusQuantity

            class NeXusAttribute(NeXusQuantity):
                comment = 'NeXus Attribute'
            self.NeXusAttribute = NeXusAttribute

            class NeXusField(NeXusQuantity):
                comment = 'NeXus Field'
            self.NeXusField = NeXusField

            class NeXusGroup(NeXusObject):
                comment = 'NeXus Group'
            self.NeXusGroup = NeXusGroup

            class NeXusUnitCategory(NeXus):
                comment = ("Unit categories in NXDL specifications describe the expected type of units for a NeXus field."
                            ""
                            "They should describe valid units consistent with"
                            "the manual section on NeXus units (based on UDUNITS)."
                            "Units are not validated by NeXus.")
                label = "NeXusUnitCategory"
            self.NeXusUnitCategory = NeXusUnitCategory

            class NeXusDataType(NeXus):
                comment = "any valid NeXus field or attribute type"
                label = "NeXusDataType"
            self.NeXusDataType = NeXusDataType

            class NeXusEnumerations(NeXus):
                comment = "Vocabulary used in NeXus enumerations"
                label = "NeXusEnumerations"
            self.NeXusEnumerations = NeXusEnumerations

            owlready2.AllDisjoint([NeXusDataType,NeXusUnitCategory,NeXusEnumerations,NeXusObject])
            owlready2.AllDisjoint([NeXusQuantity,NeXusBaseClass,NeXusApplicationClass])
            owlready2.AllDisjoint([NeXusGroup,NeXusQuantity,NeXusApplicationClass])
            owlready2.AllDisjoint([NeXusField,NeXusAttribute])

            class extends(owlready2.AnnotationProperty):
                pass

            class has(NeXusObject >> NeXusObject):
                comment = 'A representation of a "has a" relationship.'
            self.has = has
            class actualValue(owlready2.DataProperty):
                domain = [NeXus]
            self.actualValue = actualValue
            class hasValueContainer(owlready2.FunctionalProperty, NeXusQuantity >> NeXusDataType):
                comment = 'Representation of having a Value assigned.'
            self.hasValueContainer = hasValueContainer
            class hasUnitContainer(owlready2.FunctionalProperty, NeXusQuantity >> NeXusUnitCategory):
                comment = 'Representation of having a Unit assigned.'
            self.hasUnitContainer = hasUnitContainer
            class hasEnumContainer(owlready2.FunctionalProperty, NeXusQuantity >> NeXusEnumerations):
                comment = 'Representation of having an Enumeration assigned.'
            self.hasEnumContainer = hasEnumContainer
            owlready2.AllDisjoint([has,hasValueContainer,hasUnitContainer,hasEnumContainer])

    def __set_is_a_or_equivalent(self, subclass, superclass):
        def get_restriction_set(owl_class):
            return set(str(x) for x in owl_class.is_a)
        def has_diff_relations(subclass, superclass):
            return len(get_restriction_set(subclass) - get_restriction_set(superclass)) > 0
        def has_oneof_relation(owl_class):
            return "OneOf([" in str([str(x) for x in owl_class.is_a])

        if subclass.comment[0] != "" or has_diff_relations(subclass, superclass) or has_oneof_relation(subclass):
            subclass.is_a.append(superclass)

            # To show that we override values we need to add an exception to the base class if the subclass overrides it in NeXus.
            # Example where NXarpes/../probe overrides NXsource/probe's enumeration list. The syntax below is the protege syntax.
            #         The list in the curly brackets shows a OneOf relationship. 
            # NXsource/probe and (not (NXarpes/ENTRY/INSTRUMENT/SOURCE/probe)) SubClassOf {NXsource/probe/electron , NXsource/probe/muon , NXsource/probe/neutron , NXsource/probe/positron , NXsource/probe/proton , NXsource/probe/ultraviolet , NXsource/probe/x-ray , 'NXsource/probe/visible light'}
        else:
            subclass.equivalent_to.append(superclass)

    def __set_has_a_relationships(self, path, xml_tag, nx_class, parent_tag):
                parent = path[:path.rfind("/")]
                if "/" not in parent: # is either base class or appdef
                    if parent in self.nxdl_info["base_classes"]:
                        self.nxdl_info["base_classes"][parent]["onto_class"].is_a.append(self.has.min(self.nxdl_info[xml_tag][path]["minOccurs"], nx_class))
                        if self.nxdl_info[xml_tag][path]["maxOccurs"]:
                            self.nxdl_info["base_classes"][parent]["onto_class"].is_a.append(self.has.max(self.nxdl_info[xml_tag][path]["maxOccurs"], nx_class))
                    else:
                        self.nxdl_info["applications"][parent]["onto_class"].is_a.append(self.has.min(self.nxdl_info[xml_tag][path]["minOccurs"], nx_class))
                        if self.nxdl_info[xml_tag][path]["maxOccurs"]:
                            self.nxdl_info["applications"][parent]["onto_class"].is_a.append(self.has.max(self.nxdl_info[xml_tag][path]["maxOccurs"], nx_class))
                else:
                    self.nxdl_info[parent_tag][parent]["onto_class"].is_a.append(self.has.min(self.nxdl_info[xml_tag][path]["minOccurs"], nx_class))
                    if self.nxdl_info[xml_tag][path]["maxOccurs"]:
                        self.nxdl_info[parent_tag][parent]["onto_class"].is_a.append(self.has.max(self.nxdl_info[xml_tag][path]["maxOccurs"], nx_class))

    def get_unit_categories(self):
        with self.__onto__:
            unit_categories = nxdl.load_unit_categories()
            for unit in unit_categories.keys():
                nx_unit = types.new_class(unit, (self.NeXusUnitCategory,))
                nx_unit.set_iri(nx_unit, self.base_iri + "#" + unit)
                nx_unit.label.append(unit)
                nx_unit.comment.append(unit_categories[unit]["doc"])
                # TODO: Figure out how to add examples to the ontology
                # nx_unit.example.extend(unit_categories[unit]["examples"])  
                web_page = self.web_page_base_prefix + "nxdl-types.html#" + unit.lower().replace("_", "-")
                nx_unit.seeAlso.append(web_page)
                unit_categories[unit]["onto_class"] = nx_unit
            owlready2.AllDisjoint([v["onto_class"] for k,v in unit_categories.items() if k not in ["NX_ANY", "NX_TRANSFORMATION", "NX_TIME_OF_FLIGHT", "NX_UNITLESS", "NX_DIMENSIONLESS"]])
        return unit_categories


    def get_data_types(self):
        with self.__onto__:
            data_types = nxdl.load_data_types()
            for dtype in data_types.keys():
                # nx_dtype = types.new_class(dtype, (str,)) # TODO: This should be the appropriate Python data type.
                # owlready2.declare_datatype(nx_dtype, base_iri + "DataTypes/" + dtype, lambda x : x, lambda x : x)
                nx_dtype = types.new_class(dtype, (self.NeXusDataType,)) # TODO: This should be the appropriate Python data type.
                nx_dtype.set_iri(nx_dtype, self.base_iri + "#" + dtype)
                nx_dtype.label.append(dtype)
                nx_dtype.comment.append(data_types[dtype]["doc"])
                web_page = self.web_page_base_prefix + "nxdl-types.html#" + dtype.lower().replace("_", "-")
                nx_dtype.seeAlso.append(web_page)
                data_types[dtype]["onto_class"] = nx_dtype       
            owlready2.AllDisjoint([v["onto_class"] for k,v in data_types.items()])
            data_types["NX_CHAR"]["onto_class"].is_a.append(self.actualValue.some(str))  
            data_types["NX_INT"]["onto_class"].is_a.append(self.actualValue.some(int))  
            data_types["NX_FLOAT"]["onto_class"].is_a.append(self.actualValue.some(float))  
            data_types["NX_BOOLEAN"]["onto_class"].is_a.append(self.actualValue.some(bool))  
            data_types["NX_NUMBER"]["onto_class"].is_a.append(owlready2.Or([self.actualValue.some(int),self.actualValue.some(float)]))
        return data_types

    def gen_classes(self):
        with self.__onto__:
            for base_or_app in ("base_classes", "applications"):
                for class_name in self.nxdl_info[base_or_app].keys():
                    nx_class = types.new_class(class_name, (self.NeXusBaseClass if base_or_app == "base_classes" else self.NeXusApplicationClass,))
                    nx_class.set_iri(nx_class, self.base_iri + "#" + class_name) # use agreed term iri
                    self.nxdl_info[base_or_app][class_name]['onto_class'] =  nx_class    # add class to dict 
                    nx_class.comment.append(self.nxdl_info[base_or_app][class_name]['doc'])
                    nx_class.label.append(class_name)
                    web_page = self.web_page_prefix + self.nxdl_info[base_or_app][class_name]["category"] + "/" + class_name + '.html'                        
                    nx_class.seeAlso.append(web_page)
                    if "deprecated" in self.nxdl_info[base_or_app][class_name].keys():
                        nx_class.deprecated.append(True)
                        
            for base_or_app in ("base_classes", "applications"):
                for class_name in self.nxdl_info[base_or_app].keys():
                    # TODO: replace this extends with __set_is_a_or_equivalent()
                    if "extends" in self.nxdl_info[base_or_app][class_name].keys() and self.nxdl_info[base_or_app][class_name]['extends'] is not None:
                        nx_class = self.nxdl_info[base_or_app][class_name]['onto_class']
                        base = self.nxdl_info[base_or_app][class_name]['extends']
                        nx_class.extends.append(base)
                        if base_or_app == "applications" and base != "NXobject":
                            nx_class.is_a.append(self.nxdl_info["applications"][base]["onto_class"])
                        elif base_or_app == "base_classes":
                            nx_class.is_a.append(self.nxdl_info["base_classes"][base]["onto_class"])


    def get_parent(self,child_type,child):
        superclass_type = None
        superclass_path = None
        pclass_super = None
        if "superclass_path" in self.nxdl_info[child_type][child].keys():
            superclass_path = self.nxdl_info[child_type][child]["superclass_path"]
            try:
                if superclass_path in self.nxdl_info[child_type].keys():
                    superclass_type = child_type
                else:
                    superclass_type = "base_classes"
                pclass_super = self.nxdl_info[superclass_type][superclass_path]["onto_class"]
            except KeyError:
                print("Warning: " + child + " is not of same type as " + superclass_path)
        return superclass_type, superclass_path, pclass_super

    def __unique_enum_slug(self, enum_name):
        slug = _slugify(enum_name)
        unique_slug = slug
        n = 2
        while unique_slug in self.__used_enum_slugs__:
            unique_slug = f"{slug}-{n}"
            n += 1
        self.__used_enum_slugs__.add(unique_slug)
        return unique_slug

    def gen_children(self):
        classes = {"group": self.NeXusGroup, "field": self.NeXusField, "attribute": self.NeXusAttribute}
        for child_type in ("group", "field", "attribute"):        
            for child in self.nxdl_info[child_type].keys():
                nx_child = types.new_class(child, (classes[child_type],))
                nx_child.set_iri(nx_child, self.base_iri + "#" + child.lower().replace("/", "-").replace("_", "-") + "-" + child_type)
                nx_child.label.append(child)
                self.nxdl_info[child_type][child]["onto_class"] = nx_child
                nx_child.comment.append(self.nxdl_info[child_type][child]["comment"])
                web_page = self.web_page_prefix + self.nxdl_info[child_type][child]["category"] + "/" + child.split("/")[0] + ".html#"+child.lower().replace("/", "-").replace("_", "-") + "-" + child_type
                nx_child.seeAlso.append(web_page)
                if self.nxdl_info[child_type][child]["deprecated"] is not None:
                    nx_child.deprecated.append(True)
                self.__set_has_a_relationships(child, child_type, nx_child, "group" if child[:child.rfind("/")] in self.nxdl_info["group"] else "field")
            
                if child_type in ("field", "attribute"):
                    if "enums" in self.nxdl_info[child_type][child]:
                        enums = []
                        for enum in self.nxdl_info[child_type][child]["enums"]:
                            enum_name = child + "/" + enum
                            enum_cls = types.new_class(enum_name, (self.NeXusEnumerations,))
                            enum_cls.set_iri(enum_cls, self.base_iri + "#" + self.__unique_enum_slug(enum_name) + "-enum")
                            enum_cls.label.append(enum_name)
                            enum_cls.comment.append("Enumeration item for " + child + ": " + enum)
                            enum_cls.seeAlso.append(web_page)
                            enum_cls.is_a.append(self.actualValue.only(owlready2.OneOf([enum])))
                            enums.append(enum_cls)
                            self.enums[enum_name] = {"onto_class": enum_cls}
                        #TODO: add child/custom for open enums to enums as an option
                        owlready2.AllDisjoint(enums)
                        nx_child.is_a.append(self.hasEnumContainer.only(owlready2.Or(enums)))
                    else:
                        nx_child.is_a.append(self.hasValueContainer.some(self.data_types[self.nxdl_info[child_type][child]["type"]]["onto_class"]))
                        nx_child.is_a.append(self.hasValueContainer.max(0,owlready2.Not(self.data_types[self.nxdl_info[child_type][child]["type"]]["onto_class"])))
                        # TODO: Add unit category concept also for those given by an example unit
                        # for now we skip them
                        if child_type == "field":
                            unit = self.nxdl_info[child_type][child]["unit_category"]
                            if unit in self.unit_categories:
                                nx_child.is_a.append(self.hasUnitContainer.some(self.unit_categories[unit]["onto_class"]))
                            else:
                                nx_child.is_a.append(self.hasUnitContainer.some(self.unit_categories["NX_ANY"]["onto_class"]))

            # cleaning enum restrictions in superclass
            for child in self.nxdl_info[child_type].keys():
                nx_child = self.nxdl_info[child_type][child]["onto_class"]
                if child_type in ("field", "attribute"):
                    if "enums" in self.nxdl_info[child_type][child]:
                        act_type, act_child = child_type, child
                        superclass_type, superclass_path, pclass_super = self.get_parent(act_type,act_child)
                        while  pclass_super is not None:
                            #if it has enum, replace the condition
                            fnd = False
                            for restriction in pclass_super.is_a:
                                if "hasEnumContainer" in str(restriction):
                                    fnd = True
                                    pclass_super.is_a.remove(restriction)
                                    pclass_super.is_a.append(owlready2.Or([restriction,self.nxdl_info[child_type][child]["onto_class"]]))
                                    break
                            if fnd:
                                break
                            act_type, act_child = superclass_type, superclass_path
                            superclass_type, superclass_path, pclass_super = self.get_parent(act_type,act_child)

        for child_type in ("group", "field", "attribute"):        
            for child in self.nxdl_info[child_type].keys():
                superclass_type, superclass_path, pclass_super = self.get_parent(child_type,child)
                if pclass_super:
                    self.__set_is_a_or_equivalent(self.nxdl_info[child_type][child]["onto_class"], pclass_super)


    # Instances - Dataset
    def gen_datasets(self):
        dataset="dataset_000/"

        value = self.data_types["NX_CHAR"]["onto_class"]()
        value.actualValue = ["Key something"]
        value.set_iri(self.base_iri + "/testdata#" + f"{str(value.__class__).split('definitions.')[-1]}-{value.actualValue[0]}")

        valueInt = self.data_types["NX_INT"]["onto_class"]()
        valueInt.actualValue = [123]
        valueInt.set_iri(self.base_iri + "/testdata#" + f"{str(valueInt.__class__).split('definitions.')[-1]}-{valueInt.actualValue[0]}")

        valueFloat = self.data_types["NX_FLOAT"]["onto_class"]()
        valueFloat.actualValue = [123.456]
        valueFloat.set_iri(self.base_iri + "/testdata#" + f"{str(valueFloat.__class__).split('definitions.')[-1]}-{valueFloat.actualValue[0]}")

        unit1 = self.unit_categories["NX_ANY"]["onto_class"]()
        unit1.actualValue = ["keV"]
        unit1.set_iri(self.base_iri + "/testdata#" + f"{str(unit1.__class__).split('definitions.')[-1]}-{unit1.actualValue[0]}")

        valueEnumDef = self.enums["NXiv_temp/ENTRY/definition/NXiv_temp"]["onto_class"]()
        valueEnumDef.actualValue = ["NXiv_temp"]
        valueEnumDef.set_iri(self.base_iri + "/testdata#" + f"{str(valueEnumDef.__class__).split('definitions.')[-1]}1")

        name = self.nxdl_info["field"]["NXsensor/name"]["onto_class"]()
        name.label.append(dataset+"NXiv_temp/ENTRY/INSTRUMENT/ENVIRONMENT/current_sensor/name")
        name.set_iri(self.base_iri + "/testdata#" + f"{name.label[0].replace('/','-')}")
        name.hasValueContainer = value
        name.hasUnitContainer = unit1

        ltv = self.nxdl_info["field"]["NXsensor/low_trip_value"]["onto_class"]()
        ltv.label.append(dataset+"NXiv_temp/ENTRY/INSTRUMENT/ENVIRONMENT/current_sensor/low_trip_value")
        ltv.set_iri(self.base_iri + "/testdata#" + f"{ltv.label[0].replace('/','-')}")
        ltv.hasValueContainer = valueFloat
        ltv.hasUnitContainer = unit1

        current_sensor = self.nxdl_info["group"]["NXiv_temp/ENTRY/INSTRUMENT/ENVIRONMENT/current_sensor"]["onto_class"]()
        current_sensor.label.append(dataset+"NXiv_temp/ENTRY/INSTRUMENT/ENVIRONMENT/current_sensor")
        current_sensor.set_iri(self.base_iri + "/testdata#" + f"{current_sensor.label[0].replace('/','-')}")
        current_sensor.has = [name,ltv]

        environment = self.nxdl_info["group"]["NXiv_temp/ENTRY/INSTRUMENT/ENVIRONMENT"]["onto_class"]()
        environment.label.append(dataset+"NXiv_temp/ENTRY/INSTRUMENT/ENVIRONMENT")
        environment.set_iri(self.base_iri + "/testdata#" + f"{environment.label[0].replace('/','-')}")
        environment.has = [current_sensor]

        instrument = self.nxdl_info["group"]["NXiv_temp/ENTRY/INSTRUMENT"]["onto_class"]()
        instrument.label.append(dataset+"NXiv_temp/ENTRY/INSTRUMENT")
        instrument.set_iri(self.base_iri + "/testdata#" + f"{instrument.label[0].replace('/','-')}")
        instrument.has = [environment]
        
        definition = self.nxdl_info["field"]["NXiv_temp/ENTRY/definition"]["onto_class"]()
        definition.label.append(dataset+"NXiv_temp/ENTRY/definition")
        definition.set_iri(self.base_iri + "/testdata#" + f"{definition.label[0].replace('/','-')}")
        definition.hasEnumContainer = valueEnumDef
        
        entry = self.nxdl_info["group"]["NXiv_temp/ENTRY"]["onto_class"]()
        entry.label.append(dataset+"NXiv_temp/ENTRY")
        entry.set_iri(self.base_iri + "/testdata#" + f"{entry.label[0].replace('/','-')}")
        entry.has = [instrument,definition]

        appdef = self.nxdl_info["applications"]["NXiv_temp"]["onto_class"]()
        appdef.label.append(dataset+"NXiv_temp")
        appdef.set_iri(self.base_iri + "/testdata#" + f"{appdef.label[0].replace('/','-')}")
        appdef.has = [entry]

        root = self.nxdl_info["base_classes"]["NXroot"]["onto_class"]()
        root.label.append(dataset)
        root.set_iri(self.base_iri + "/testdata#" + f"{root.label[0].replace('/','-')}")
        root.has = [entry]


        # introducing contradictions
        
        # different datatypes
        # ltv.hasValue.append(valueInt)
        # ltv.hasValue.append(value)

        # wrong enums
        # definition.actualValue = ["still bad"]

        valueEnumDef2 = self.enums["NXsensor_scan/ENTRY/definition/NXsensor_scan"]["onto_class"]()
        valueEnumDef2.actualValue = ["NXsensor_scan"]
        valueEnumDef2.set_iri(self.base_iri + "/testdata#" + f"{str(valueEnumDef2.__class__).split('definitions.')[-1]}1")

        valueEnumDef3 = self.enums["NXapm/ENTRY/definition/NXapm"]["onto_class"]()
        valueEnumDef3.actualValue = ["NXapm"]
        valueEnumDef3.set_iri(self.base_iri + "/testdata#" + f"{str(valueEnumDef3.__class__).split('definitions.')[-1]}1")

        # definition.hasEnumContainer = valueEnumDef3


