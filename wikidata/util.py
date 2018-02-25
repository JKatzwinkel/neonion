
from annotationsets.models import Concept

import wiki
import views


#related_types_query = 'values ?entity {{{entities}}} . {{ ?subj ?p ?entity ; wdt:P31 ?item}} union {{?entity ?p ?obj . ?obj wdt:P31 ?item}}'
related_types_query = '''values ?entity {{{entities}}} .
    {{ ?obj ?p ?entity ;
             wdt:P31 ?item}}
    union {{
        ?entity ?p ?obj .
        ?obj wdt:P31 ?item
        MINUS {{ ?entity wdt:P279 ?obj }} }}'''

superclasses_query = '''values ?type {{{types}}} .
    {{ ?type wdt:P279 ?supertype }}
    union
    {{ ?type wdt:P31 ?supertype }}'''


def make_value_list(qids):
    return ' '.join(['wd:'+q for q in qids])


def count(type_support_record):
    return sum([len(objects) for prop,objects in type_support_record.items()])



def types_related_to_entity_list(entities, concept_id, user_id):
    """ takes a list of wikidata item page IDs, retrieves a bunch of statements involving those,
    and extracts the classes of which related items are instances of. """

    res = wiki.sparql(related_types_query.format(entities=make_value_list(entities)))

    types = {}
    for i in res:
        record = types.get(i['item']['value'], {})
        record[i['p']['value']] = record.get(i['p']['value'], []) + [i['obj']['value']]
        types[i['item']['value']] = record

    res = wiki.sparql(superclasses_query.format(
        types=make_value_list([t.split('/')[-1] for t in types.keys()])))

    for i in res:
        record = types.get(i['supertype']['value'], {})
        p = 'https://www.wikidata.org/wiki/Property:P279'
        record[p] = record.get(p, []) + [i['type']['value']]
        types[i['supertype']['value']] = record

    ret = types
    for t,rec in types.items():
        ret[t]['count'] = count(rec)
    #ret = sorted([(k,v) for k,v in ret.items()], key=count)


    return {
            "concept_id": concept_id,
            "user_id": user_id,
            "related_types": ret
            }







