import json
import uuid

from elasticsearch import Elasticsearch
import wiki


es = Elasticsearch('http://127.0.0.1:9200')


related_things_query = '''values ?entity {{{entities}}}
  {{?obj ?pr ?entity;
        wdt:P31 ?objecttype }}
  union {{?entity ?p ?obj.
         optional {{?obj wdt:P31 ?objecttype. }}
        }}
  minus {{ values ?p {{ wdt:P31 }} }}'''
#  minus {{ values ?objecttype {{ wd:Q4167836 }} }}

taxo_query = '''select ?type ?supertype where {{
  values ?type {{{}}} .
  values ?supertype {{{}}} .
  ?type wdt:P279 ?supertype . }}'''


def make_value_list(qids):
    """ takes a list of Wikidata item page IDs, removes redundant items, and puts a `wd:` prefix in front of each of them."""
    return ' '.join(['wd:'+wiki.extract_id(q) for q in set(qids) if q])


def suuid(statement):
    """ takes a statement that has subject (s), predicate (p), and an object (o) being an instance of a type (t)
    and generates a UUID for this particular combination. """
    md5 = uuid.uuid3(uuid.NAMESPACE_URL,
            u'{} {} {} {}'.format(*[statement.get(pos) for pos in 'spot']).encode('ascii','replace'))
    return u'{}'.format(md5)


def es_index_name(conceptset, doctype):
    """ return index name for given concept set name. """
    return '{}-{}'.format(conceptset, doctype)


def store(conceptset, doctype, body):
    """ stores object in elasticsearch index. creates index if required. Expects object to have a unique ID in an `id` field. """
    if not es.indices.exists(es_index_name(conceptset, doctype)):
        es.indices.create(index=es_index_name(conceptset, doctype), ignore=400)
    es.index(index=es_index_name(conceptset, doctype), doc_type=doctype, body=body, id=body.get('id'), refresh=True)


def search(conceptset, doctype, query):
    """ searches the specified index for objects matching the given Lucene query (e.g. 'p:P20'). """
    results = es.search(es_index_name(conceptset, doctype), doctype, q=query, size=1000)
    return results.get('hits', {}).get('hits')


def lookup_term_record(conceptset, doctype, termid):
    """ retrieves a terminological record from elasticsearch. just give the term (type/property) ID.
    if it can't be found, an almost empty dictionary with nothing but the given ID in it is returned. """
    hits = search(conceptset, doctype, 'id:{}'.format(termid))
    if len(hits) > 0:
        return [hit.get('_source', {}) for hit in hits if hit.get('_id') == termid][0]
    else:
        return {'id': termid}


def extract_descriptive_terminology(conceptset, concept_id, entity):
    """ takes an entity in form of a wikidata item page URL or ID and retrieves the vocabulary used to describe that
    entity, i.e. the properties used in statements in which the entity is involved, and the types (P31) of the related
    items that co-occur with the entity in these statements.
    In a second step, some taxonomic structure is extracted from the retrieved types by querying each type's superclasses (P279).
    """
    qid = wiki.extract_id(entity)
    statements = []
    properties = {}
    if qid:
        data = wiki.sparql(related_things_query.format(entities=make_value_list([qid])))
        for row in data:
            statement = {
                's': row.get('entity', {}).get('value'),
                'c': u'{}'.format(concept_id), # ID part of related_concept URL , like e.g. `Q5`
                'p': row.get('p', row.get('pr')).get('value'),
                'o': row.get('obj').get('value'),
                't': row.get('objecttype', {}).get('value', u'null')}
            statement = {k:wiki.extract_id(v) for k,v in statement.items()}
            statement['id'] = suuid(statement)
            statements.append(statement)
            # save to elasticsearch index
            store(conceptset, 'statement', statement)
            # add object type to list of types encountered via the determined property regardless of direction
            #properties[statement['p']] = properties.get(statement['p'],[]) + [statement.get('t')]
            # register type occurence under statement uuid in property record while preserving direction of relation
            prop = wiki.extract_id(row.get('p', {}).get('value'))
            if prop:
                property_occurence = properties.get(prop, {})
                property_occurence[concept_id] = property_occurence.get(concept_id, {})
                property_occurence[concept_id][statement['id']] = {
                    'object': statement.get('o'),
                    'object_type': statement.get('t')}
                property_occurence['id'] = prop
                properties[prop] = property_occurence
                #store('property', property_occurence, conceptset)

    # extract actual types from statements
    types = [statement.get('t') for statement in statements if 't' in statement and statement.get('t').lower().startswith('q')]
    value_list = make_value_list(types)
#print(taxo_query.format(value_list, value_list))
    taxonomical = wiki.sparql(taxo_query.format(value_list, value_list))
#print(taxonomical)
    taxonomy = {}
    for taxonode in taxonomical:
        typeid = wiki.extract_id(taxonode.get('type').get('value'))
        superid = wiki.extract_id(taxonode.get('supertype').get('value'))
        #
        # first look in volatile dictionary registry, query elasticsearch as a fallback if that doesn't work
        term_record = taxonomy.get(superid, lookup_term_record(conceptset, 'term', superid))
        term_record['narrower'] = term_record.get('narrower',[]) + [typeid]
        term_record['id'] = superid
        taxonomy[superid] = term_record
        # same for subtype/narrower type of the two involved in hierarchical relation
        term_record = taxonomy.get(typeid, lookup_term_record(conceptset, 'term', typeid))
        term_record['broader'] = term_record.get('broader',[]) + [superid]
        term_record['id'] = typeid
        taxonomy[typeid] = term_record

    for typeid, term_record in taxonomy.items():
        for k in ['narrower', 'broader']:
            term_record[k] = list(set(term_record.get(k, [])))
        store(conceptset, 'term', term_record)





def properties_ranked(conceptset, query=None):
    """ extracts all properties from the statements that have been harvested from wikidata in order to gather
    terminological knowledge / descriptive terminology about the specific entities that have been identified
    by users so far. """
    hits = [hit.get('_source') for hit in search(conceptset, 'statement', query)]
    properties = {}
    for hit in hits:
        p = hit.get('p')
        properties[p] = properties.get(p, []) + [hit]
    return properties


def faceted_statements(conceptset, particles, query=None):
    """ by specifying a sequence of characters identifying the one-char keys of statement objects as stored in elasticsearch,
    we can define a faceted structure in which the information from all statements matching an optional query will be retrieved.
    Example: if you pass `particles='tp'`, a dictionary will be returned with object types as keys and another level of dictionaries
    as values, at which properties will be the keys and a list of statementsthe values. """
    hits = [hit.get('_source') for hit in search(conceptset, 'statement', query)]
    return _faceted(hits, particles)


def _faceted(hits, particles):
    """ recursive helper function for faceted retrieval of statements. """
    records = {}
    particle = particles[0]
    for hit in hits:
        p = hit.get(particle)
        records[p] = records.get(p, []) + [{key:hit.get(key) for key in hit.keys() if not key == particle}]
    if len(particles) > 1:
        for key in records.keys():
            records[key] = _faceted(records.get(key), particles[1:])
    return records


def print_facet(faceted_record, indent=0):
    for key, rec in faceted_record.items():
        print(u'{}{} ({})'.format(' '*indent, wiki.label(key), key))
        if type(rec) is dict:
            print_facet(rec, indent=indent+1)
        elif type(rec) is list:
            for entry in rec:
                print(u'{} {}'.format(' '*indent, ' '.join(['{}:{}'.format(k,v) for k,v in entry.items() if not k == 'id'])))




def sort_dict(dictionary):
    """ takes a dictionary and makes in into a list of (k,v) tuples and sorts by len(v) in descending order. """
    return sorted(dictionary.items(), key=lambda t:len(t[1]), reverse=True)



