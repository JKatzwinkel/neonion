import requests
import json

from urllib import urlencode

# [{
#     "viaf": ["113230702"],
#     "birth": "1952-03-11",
#     "descr": "English writer and humorist",
#     "label": "Douglas Adams",
#     "gnd": ["119033364"],
#     "id": "Q42",
#     "aliases": ["Douglas No\u00ebl Adams", "Douglas Noel Adams", "DNA", "Bop Ad"]
# }]
#https: // www.wikidata.org / w / api.php\?action\=wbsearchentities\ & language\=en\ & search\=Reinhard % 20
#Heydrich\ & format\=json\ & uselang\=en



query_temp = "https://www.wikidata.org/w/api.php?action=wbsearchentities&language=en&format=json&uselang=en&{}"

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


        #return [{"viaf": ["113230702"], "birth": "1952-03-11", "descr": "English writer and humorist", "label": "Douglas Adams", "gnd": ["119033364"], "id": "Q42", "aliases": ["Douglas No\u00ebl Adams", "Douglas Noel Adams", "DNA", "Bop Ad"]}]
