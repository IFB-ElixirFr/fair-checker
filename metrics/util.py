from SPARQLWrapper import SPARQLWrapper, N3, JSON, RDF, TURTLE, JSONLD
from rdflib import Graph, ConjunctiveGraph, Namespace
from rdflib.namespace import RDF
import requests
from jinja2 import Template
from pyshacl import validate
import extruct
import json

from lxml import html
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

import re

# DOI regex
regex = r"10.\d{4,9}\/[-._;()\/:A-Z0-9]+"

# Describe datacite
def describe_opencitation(uri, g):
    # g = Graph()
    print(f'SPARQL for [ {uri} ] with enpoint [ Opencitation ]')
    sparql = SPARQLWrapper("https://opencitations.net/sparql")
    sparql.setQuery("""
            PREFIX cito: <http://purl.org/spar/cito/>
            PREFIX dcterms: <http://purl.org/dc/terms/>
            PREFIX datacite: <http://purl.org/spar/datacite/>
            PREFIX literal: <http://www.essepuntato.it/2010/06/literalreification/>
            PREFIX biro: <http://purl.org/spar/biro/>
            PREFIX frbr: <http://purl.org/vocab/frbr/core#>
            PREFIX c4o: <http://purl.org/spar/c4o/>

            DESCRIBE ?x WHERE {
                ?x datacite:hasIdentifier/literal:hasLiteralValue '""" + uri + """'
            }
    """)

    sparql.setReturnFormat(TURTLE)
    results = sparql.query().convert()
    print("Results: " + str(len(results)))

    results = results.serialize(format='turtle').decode()

    g.parse(data=results, format="turtle")

    # print(g.serialize(format='turtle').decode())
    return g

# Describe lod.openaire
def describe_loa(uri, g):
    # g = Graph()
    print(f'SPARQL for [ {uri} ] with enpoint [ LOA ]')
    sparql = SPARQLWrapper("http://lod.openaire.eu/sparql")
    sparql.setQuery("""
            DESCRIBE ?x WHERE {
            ?x <http://lod.openaire.eu/vocab/resPersistentID> '""" + uri + """'
            }
    """)

    g_len = Graph()
    sparql.setReturnFormat(N3)
    results = sparql.query().convert()
    print("Results: " + str(len(g_len.parse(data=results, format="n3"))))
    g.parse(data=results, format="n3")

    # print(g.serialize(format='turtle').decode())
    return g


# Describe Wikidata
def describe_wikidata(uri, g):
    # g = Graph()
    print(f'SPARQL for [ {uri} ] with enpoint [ Wikidata ]')
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    sparql.setQuery("""
            PREFIX wd: <http://www.wikidata.org/entity/>
            PREFIX wdt: <http://www.wikidata.org/prop/direct/>
            PREFIX wikibase: <http://wikiba.se/ontology#>
            PREFIX p: <http://www.wikidata.org/prop/>
            PREFIX ps: <http://www.wikidata.org/prop/statement/>
            PREFIX pq: <http://www.wikidata.org/prop/qualifier/>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX bd: <http://www.bigdata.com/rdf#>

            DESCRIBE ?x WHERE {
                ?x wdt:P356 '""" + uri + """'
            }
    """)

    sparql.setReturnFormat(N3)
    results = sparql.query().convert()
    print("Results: " + str(len(results)))
    results = results.serialize(format='turtle').decode()

    g.parse(data=results, format="n3")

    # print(g.serialize(format='turtle').decode())
    return g

# Describe a tool based on experimental bio.tools SPARQL endpoint
def describe_biotools(uri, g):
    print(f'SPARQL for [ {uri} ] with enpoint [ bio.tools ]')

    h = {'Accept': 'text/turtle'}
    p = {'query': "DESCRIBE <" + uri + ">"}
    res = requests.get("https://134.158.247.76/sparql", headers=h, params=p, verify=False)

    g.parse(data=res.text, format="turtle")

    #print(g.serialize(format='turtle').decode())
    return g


def is_DOI(uri):
    return bool(re.search(regex, uri, re.MULTILINE | re.IGNORECASE))

def get_DOI(uri):
    match = re.search(regex, uri, re.MULTILINE | re.IGNORECASE)
    return match.group(0)

def ask_OLS(uri):
    """
    Checks that the URI is registered in one of the ontologies indexed in OLS.
    :param uri:
    :return: True if the URI is registered in one of the ontologies indexed in OLS, False otherwise.
    """
    print(f'call to the OLS REST API for [ {uri} ]')
    h = {'Accept': 'application/json'}
    p = {'iri': uri}
    res = requests.get("http://www.ebi.ac.uk/ols/api/terms", headers=h, params=p, verify=False)

    if res.json()['page']['totalElements'] > 0:
        return True
    else:
        return False

def ask_LOV(uri):
    """
    Checks that the URI is registered in one of the ontologies indexed in LOV (Linked Open Vocabularies).
    :param uri:
    :return: True if the URI is registered in one of the ontologies indexed in LOV, False otherwise.
    """
    print(f'SPARQL for [ {uri} ] with enpoint [ https://lov.linkeddata.es/dataset/lov/sparql ]')

    h = {'Accept': 'application/sparql-results+json'}
    p = {'query': "ASK { <" + uri + "> ?p ?o }"}
    res = requests.get("https://lov.linkeddata.es/dataset/lov/sparql", headers=h, params=p, verify=False)

    # print(res.text)
    # if res.text.startswith("Error 400: Parse error:"):
    #     return False
    return res.json()['boolean']

def gen_shape(property_list = None, class_list = None, recommendation=None):
    """

    @param property_list: a list of OWL/RDF properties
    @param class_list: a list of OWL/RDF classes
    @param recommendation: the message to be displayed during validation
    @return: a SHACL constraint expression to validate RDF graph based on a list or required properties or classes (at least)

    @TODO another method for strong validation (AND)
    """

    return None

def shape_checks(kg):
    """

    @param kg:
    @return:
    """

    types = ['schema:SoftwareApplication', 'schema:CreativeWork', 'schema:Dataset', 'schema:ScholarlyArticle']
    minimal_dataset_properties = ['schema:name', 'schema:description', 'schema:identifier', 'schema:keywords', 'schema:url']
    recommended_dataset_properties = ['schema:license', 'schema:creator', 'schema:citation']

    minimal_software_properties = ['schema:name', 'schema:description', 'schema:url']
    recommended_software_properties = ['schema:additionalType', 'schema:applicationCategory', 'schema:applicationSubCategory', 'schema:author' 'schema:license', 'schema:citation', 'schema:featureList', 'schema:softwareVersion']

    minimal_publication_properties = ['schema:headline', 'schema:identifier']
    recommended_publication_properties = ['schema:about', 'schema:alternateName', 'schema:author', 'schema:backstory', 'schema:citation', 'schema:dateCreated', 'schema:dateModified', 'schema:datePublished', 'schema:isBasedOn', 'schema:isPartOf', 'schema:keywords', 'schema:license', 'schema:pageEnd', 'schema:pageStart', 'schema:url']

    shape_template = """
    @prefix dash: <http://datashapes.org/dash#> .
    @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
    @prefix schema: <http://schema.org/> .
    @prefix sh: <http://www.w3.org/ns/shacl#> .
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
    @prefix edam: <http://edamontology.org/> .
    @prefix biotools: <https://bio.tools/ontology/> .

    schema:SoftwareShape
        a sh:NodeShape ;
        sh:targetClass schema:SoftwareApplication ;

        {% for prop_name in data['software_min'] %}
        sh:property [
            sh:path {{prop_name}} ;
            sh:minCount 1 ;
            sh:severity sh:Violation
        ] ;
        {% endfor %}
    .

    schema:SoftwareShape
        a sh:NodeShape ;
        sh:targetClass schema:SoftwareApplication ;

        {% for prop_name in data['software_reco'] %}
        sh:property [
            sh:path {{prop_name}} ;
            sh:minCount 1 ;
            sh:severity sh:Warning
        ] ;
        {% endfor %}
    .

    schema:DatasetShape
        a sh:NodeShape ;
        sh:targetClass schema:Dataset ;

        {% for prop_name in data['dataset_min'] %}
        sh:property [
            sh:path {{prop_name}} ;
            sh:minCount 1 ;
            sh:severity sh:Violation
        ] ;
        {% endfor %}
    .

    schema:DatasetShape
        a sh:NodeShape ;
        sh:targetClass schema:Dataset ;

        {% for prop_name in data['dataset_reco'] %}
        sh:property [
            sh:path {{prop_name}} ;
            sh:minCount 1 ;
            sh:severity sh:Warning
        ] ;
        {% endfor %}
    .

    schema:PaperShape
        a sh:NodeShape ;
        sh:targetClass schema:ScholarlyArticle ;

        {% for prop_name in data['paper_min'] %}
        sh:property [
            sh:path {{prop_name}} ;
            sh:minCount 1 ;
            sh:severity sh:Violation
        ] ;
        {% endfor %}
    .

    schema:PaperShape
        a sh:NodeShape ;
        sh:targetClass schema:ScholarlyArticle ;

        {% for prop_name in data['paper_reco'] %}
        sh:property [
            sh:path {{prop_name}} ;
            sh:minCount 1 ;
            sh:severity sh:Warning
        ] ;
        {% endfor %}
    .

    """

    data = {
        'software_min': minimal_software_properties,
        'software_reco': recommended_software_properties,
        'dataset_min': minimal_dataset_properties,
        'dataset_reco': recommended_dataset_properties,
        'paper_min': minimal_publication_properties,
        'paper_reco': recommended_publication_properties}

    template = Template(shape_template)
    shape = template.render(data=data)
    print(shape)
    g = ConjunctiveGraph()
    g.parse(data=shape, format='turtle')
    print(len(g))

    r = validate(data_graph=kg,
                 data_graph_format='turtle',
                 shacl_graph=shape,
                 # shacl_graph = my_shacl_constraint,
                 shacl_graph_format='turtle',
                 ont_graph=None,
                 inference='rdfs',
                 abort_on_error=False,
                 meta_shacl=False,
                 debug=True)

    conforms, results_graph, results_text = r

    report_query = """
        SELECT ?node ?path ?severity WHERE {
            ?v rdf:type sh:ValidationReport ;
               sh:result ?r .
            ?r sh:focusNode ?node ;
               sh:sourceShape ?s .
            ?s sh:path ?path ;
               sh:severity ?severity .
        }
    """

    results = results_graph.query(report_query)
    warnings = []
    errors = []
    for r in results:
        if "#Warning" in r['severity']:
            warnings.append(f'Property {r["path"]} <span class="has-text-warning has-text-weight-bold">should be</span> provided')
        if "#Violation" in r['severity']:
            errors.append(f'Property {r["path"]} <span class="has-text-danger has-text-weight-bold">must be</span> provided')

    return warnings, errors


def extract_rdf_from_html(uri):
    page = requests.get(uri)
    html = page.content

    d = extruct.extract(html, syntaxes=['microdata', 'rdfa', 'json-ld'], errors='ignore')
    return d

def extruct_to_rdf(extruct_str):

    g = ConjunctiveGraph()

    for md in extruct_str["json-ld"]:
        g.parse(data=json.dumps(md, ensure_ascii=False), format="json-ld")

    for md in extruct_str['rdfa']:
        g.parse(data=json.dumps(md, ensure_ascii=False), format="json-ld")

    for md in extruct_str['microdata']:
        g.parse(data=json.dumps(md, ensure_ascii=False), format="json-ld")

    return g


def rdf_to_triple_list(graph):
    tuple_list = []
    for s, p, o in graph.triples((None, None, None)):
        print("{} => {} => {}".format(s, p, o))
        tuple_list.append((str(s), str(p), str(o)))

    return tuple_list
    # for s, p, o in graph.triples((None,  RDF.type, None)):
    #     print("{} => {}".format(p, o))


def get_rdf_selenium(uri, kg):
    # uri = 'https://workflowhub.eu/workflows/45'
    #uri = 'https://bio.tools/jaspar'

    chrome_options = Options()
    chrome_options.add_argument("--headless")

    browser = webdriver.Chrome(options = chrome_options)
    browser.get(uri)

    html_source = browser.page_source
    #print(html_source)
    browser.quit()
    tree = html.fromstring(html_source)
    jsonld_string = tree.xpath('//script[@type="application/ld+json"]//text()')

    kg = ConjunctiveGraph()
    for json_ld_annots in jsonld_string :
        jsonld = json.loads(json_ld_annots)

        if '@context' in jsonld.keys():
            if ('//schema.org' in jsonld['@context']):
                jsonld['@context'] = 'static/data/jsonldcontext.json'
        kg.parse(data=json.dumps(jsonld, ensure_ascii=False), format="json-ld")

        print(f'{len(kg)} retrieved triples in KG')
        print(kg.serialize(format='turtle').decode())

    return kg

def get_html_selenium(uri):
    # uri = 'https://workflowhub.eu/workflows/45'
    #uri = 'https://bio.tools/jaspar'

    chrome_options = Options()
    chrome_options.add_argument("--headless")

    browser = webdriver.Chrome(options = chrome_options)
    browser.get(uri)

    html_source = browser.page_source
    #print(html_source)
    browser.quit()


    return html_source


def download_csv(uri):

    client = MongoClient()
    db = client.fair_checker
    evaluations = db.evaluations

    a_day_ago = datetime.now() - timedelta(1)
    pass
