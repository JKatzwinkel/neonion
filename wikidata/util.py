
from annotationsets.models import Concept

import wiki
import views


#related_types_query = 'values ?entity {{{entities}}} . {{ ?subj ?p ?entity ; wdt:P31 ?item}} union {{?entity ?p ?obj . ?obj wdt:P31 ?item}}'
related_types_query = '''values ?entity {{{entities}}} .
    {{ ?obj ?p ?entity ;
             wdt:P31 ?item}}
    union {{
        ?entity ?p ?obj .
        ?obj wdt:P31 ?item }}'''

superclasses_query = '''values ?type {{{types}}} .
    {{ ?type wdt:P279 ?supertype }}
    union
    {{ ?type wdt:P31 ?supertype }}'''


def make_value_list(qids):
    return ' '.join(['wd:'+q for q in qids])



def types_related_to_entity_list(entities):

    # entities = views.linked_entities_in_document(document_pk=document.id,
    #         concept_id=concept.label)
    # entities = [entity.split('/')[-1] for entity in entities]

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

    count = lambda tupel:sum([len(p) for p in tupel[1]])

    ret = sorted([(k,v) for k,v in types.items()], key=count)

    return ret







