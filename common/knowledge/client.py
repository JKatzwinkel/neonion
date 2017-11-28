import requests
import re as _re
from datetime import datetime

from urllib import urlencode

from SPARQLWrapper import SPARQLWrapper, JSON
import pywikibot as _wiki

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

    def __init__(self):
        self._site = _wiki.Site('wikidata', 'wikidata')
        self.repo =self. _site.data_repository()

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


    def create_item(self):
      """ returns a newly created item page """
      new_item = self.repo.editEntity(dict(), dict(), summary="created by script")
      if new_item.get('success'):
        qid = new_item.get('entity', {}).get('id')
        return self.item(qid)

    def create_claim(self, pid, isReference=False):
      """ Pass property identifier string (P...) """
      return _wiki.Claim(self.repo, pid, isReference=isReference)

    def add_source_url(self, claim, source):
      """ Adds given URL as a reference for specified claim and adds current date as reference as well. """
      source_claim = self.create_claim('P248' if type(source) == _wiki.page.ItemPage else 'P854', isReference=True)
      source_claim.setTarget(source)
      now = datetime.now()
      source_date = _wiki.WbTime(year=now.year, month=now.month, day=now.day)
      date_claim = self.create_claim('P813', isReference=True)
      date_claim.setTarget(source_date)
      claim.addSources([source_claim, date_claim], bot=True)
      return source_claim

    def create_date(self, date):
      """ give date in format: 'YYYY-MM-DD' """
      fields = date.split('-')
      if len(fields) == 3:
        kwargs = {key:int(fields[i]) for i,key in enumerate(['year','month','day'])}
        return _wiki.WbTime(**kwargs)
      return None


    def find_claim_source(self, sid, pid, oid, documentId):
        source_item = self.item(documentId)
        claim = self.find_claim(sid, pid, oid)
        for reference in claim.sources:
            for source in reference.get("P248", []):
                if source.getTarget().id == source_item.id:
                    print('found source!!!')
                    return source.toJSON()
        return {}

    def find_claim(self, sid, pid, oid):
        # look up a specified statement
        subj_item = self.item(sid)
        claims = subj_item.get().get('claims', {})
        for claim in claims.get(pid, []):
            if claim.getTarget().id == oid:
                print('found statement! {} -> {} -> {}'.format(sid, pid, oid))
                return claim
        return None


    def support_claim(self, sid, pid, oid, documentId):
        # provide bibliographic support for an item statement
        source_item = self.item(documentId)
        claim = self.find_claim(sid, pid, oid)
        if claim:
            source_claim =  self.add_source_url(claim, source_item)
            return source_claim.toJSON()
        return {}

    def item(self, id):
      if not id.lower().startswith('q'):
        id = extract_id(id)
      return _wiki.ItemPage(self.repo, id)

    def prop(self, id):
      if not id.lower().startswith('p'):
        id = extract_id(id)
      return _wiki.PropertyPage(self.repo, id)



def create_monolingualtext(text, lang):
    """ returns a `WbMonolingualText` object with specified text and language
    @param lang language code (en, de, ...)"""
    return _wiki.WbMonolingualText(text, lang)


def extract_id(url):
  """ Extracts item or property ID from any string."""
  return _re.findall("[PpQq][1-9][0-9]*", url)[0]



def label(entity):
  labels = entity.get().get('labels', {})
  if 'en' in labels:
    return labels.get('en')
  else:
    for v in labels.values():
      return v


