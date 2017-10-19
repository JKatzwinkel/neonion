import requests
import re as _re

from urllib import urlencode

from SPARQLWrapper import SPARQLWrapper, JSON

_sparqli = SPARQLWrapper('https://query.wikidata.org/bigdata/namespace/wdq/sparql')
_sparqli.setReturnFormat(JSON)

_query_temp = "https://www.wikidata.org/w/api.php?action=wbsearchentities&language=en&format=json&uselang=en&{}"

_itempage_urlex = _re.compile("https?://(www\.)?wikidata\.org/wiki/Q[0-9]+")

_snoopy_url = "http://138.232.66.120:11950/recommendations?properties={}"

def is_itempage_url(url):
    return _itempage_urlex.match(url)


def map_result(item):
    return {
        "descr": item.get('description',''),
        "label": item.get('label',''),
        "id": item.get('id', ''),
        "uri": item.get('concepturi', ''),
        "aliases": item.get('aliases', [])
    }

def snoopy_request(properties):
    propertystring = ';'.join(properties)
    request = requests.get(_snoopy_url.format(propertystring))
    return request.text

class WikidataClient(object):

    def search(self, term, type):
        url = _query_temp.format(urlencode({"search":term}))
        response = requests.get(url)
        if response.status_code == 200:
            return map(map_result, response.json()['search'])

    def sparql(self, query, limit=500):
        _sparqli.setQuery('select * where {{{}}} limit {}'.format(query, limit))
        results = _sparqli.query().convert()
        return results.get('results', {}).get('bindings', [])

    def extract_id(self, url):
      """ Extracts item or property ID from any string."""
      return _re.findall("[PpQq][1-9][0-9]*", url)[0]

