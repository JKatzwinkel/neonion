import requests
import re

from urllib import urlencode

from SPARQLWrapper import SPARQLWrapper, JSON

_sparqli = SPARQLWrapper('https://query.wikidata.org/bigdata/namespace/wdq/sparql')
_sparqli.setReturnFormat(JSON)

query_temp = "https://www.wikidata.org/w/api.php?action=wbsearchentities&language=en&format=json&uselang=en&{}"

_itempage_urlex = re.compile("https?://(www\.)?wikidata\.org/wiki/Q[0-9]+")


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

class WikidataClient(object):

    def search(self, term, type):
        url = query_temp.format(urlencode({"search":term}))
        response = requests.get(url)
        if response.status_code == 200:
            return map(map_result, response.json()['search'])

    def sparql(query, limit=500):
        _sparqli.setQuery('select * where {{{}}} limit {}'.format(query, limit))
        results = _sparqli.query().convert()
        return results.get('results', {}).get('bindings', [])

