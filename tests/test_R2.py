import unittest
from lxml import html
import requests
import json
import rdflib
from rdflib import ConjunctiveGraph
from rdflib.compare import to_isomorphic, graph_diff
import pyshacl
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import extruct

from metrics.R2Impl import R2Impl


###
### TODO check this issue https://github.com/RDFLib/rdflib-jsonld/issues/84
###
class R2ImplTestCase(unittest.TestCase):
    # def setUp(self):

    uri_test = 'https://workflowhub.eu/workflows/45'

    def test_extract_html_requests(self):
        class_r2 = R2Impl()
        class_r2.set_url(self.uri_test)
        class_r2.extract_html_requests()
        requests_status_code = class_r2.get_requests_status_code()
        self.assertEqual(200, requests_status_code)

    def test_extract_rdf(self):
        class_r2 = R2Impl()
        class_r2.set_url(self.uri_test)
        class_r2.extract_html_requests()
        class_r2.extract_rdf()
        self.assertEqual(83, len(class_r2.get_jsonld()))

    def test_R2_Impl(slef):
        class_r2 = R2Impl()
        print(class_r2.get_name())
        uri = 'https://workflowhub.eu/workflows/45'
        # uri = "https://data.inrae.fr/dataset.xhtml?persistentId=doi:10.15454/A4KXE7"
        class_r2.set_url(uri)
        class_r2.extract_html_requests()
        # class_r2.extract_html_selenium()
        # print(class_r2.get_html_source())
        class_r2.extract_rdf()
        print("Classes:")
        for rdf_class in class_r2.get_classes():
            print(str(rdf_class[0]))


        print("\nProperties:")
        for rdf_prop in class_r2.get_properties():
            print(str(rdf_prop[0]))
            print(class_r2.ask_LOV(rdf_prop[0]))
            # for obj in class_r2.get_jsonld().objects(predicate=rdf_prop[0]):
                # print(obj)
                # if class_r2.is_valid_uri(obj):
                #     print(class_r2.ask_LOV(obj))

        # for s, p, o in class_r2.get_jsonld():
        #     print("%s : %s : %s" % (s,p,o))


    def test_dynamic_biotools(self):
        #uri = 'https://workflowhub.eu/workflows/45'
        uri = 'https://bio.tools/jaspar'

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
                    jsonld['@context'] = '../static/data/jsonldcontext.json'
            kg.parse(data=json.dumps(jsonld, ensure_ascii=False), format="json-ld")

            print(f'{len(kg)} retrieved triples in KG')
            print(kg.serialize(format='turtle').decode())

        self.assertEqual(62, len(kg))


    def test_static_data_inra(self):
        #uri = 'https://data.inrae.fr/dataset.xhtml?persistentId=doi:10.15454/GANJ7J'
        uri = 'https://workflowhub.eu/workflows/45'
        #uri = 'https://bio.tools/jaspar'

        r = requests.get(uri)
        text = r.content
        #print(text.decode())
        #d = extruct.extract(html, syntaxes=['microdata', 'rdfa', 'json-ld'], errors='ignore')
        d = extruct.extract(text, syntaxes=['microdata', 'json-ld'])
        #tree = html.fromstring(r.content)
        #print(tree.xpath('//script[@type="application/ld+json"]//text()'))
        #print(data)
        r.connection.close()

        print(d)
        kg = ConjunctiveGraph()

        for md in d['json-ld']:
            if '@context' in md.keys():
                print(md['@context'])
                if ('//schema.org' in md['@context']):
                    md['@context'] = '../static/data/jsonldcontext.json'
            #print(json.dumps(md, ensure_ascii=True, indent=True))
            kg.parse(data=json.dumps(md, ensure_ascii=True), format="json-ld")
        for md in d['microdata']:
            if '@context' in md.keys():
                if ('//schema.org' in md['@context']):
                    md['@context'] = '../static/data/jsonldcontext.json'
            kg.parse(data=json.dumps(md, ensure_ascii=False), format="json-ld")

        print(f'{len(kg)} retrieved triples in KG')
        print(kg.serialize(format='turtle').decode())
        self.assertEqual(True, True)


if __name__ == '__main__':
    unittest.main()
