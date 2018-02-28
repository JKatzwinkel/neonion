
from annotationsets.models import Concept

import wiki
import views


#related_types_query = 'values ?entity {{{entities}}} . {{ ?subj ?p ?entity ; wdt:P31 ?item}} union {{?entity ?p ?obj . ?obj wdt:P31 ?item}}'
related_types_query = '''values ?entity {{{entities}}} .
    {{ ?obj ?pr ?entity ;
             wdt:P31 ?item}}
    union {{
        ?entity ?p ?obj .
        ?obj wdt:P31 ?item
        MINUS {{ ?entity wdt:P279 ?obj }} }}'''

superclasses_query = '''values ?type {{{types}}} .
    {{ ?type wdt:P279 ?supertype }}
    union
    {{ ?type wdt:P31 ?supertype }}'''

def median(struct):
    l=sorted([(k,v) for k,v in struct.items()], key=lambda kv:len(kv[1]))
    return l[int(len(l)/2)]


def make_value_list(qids):
    return ' '.join(['wd:'+q for q in qids])


def count(type_support_record):
    return sum([len(objects) for prop,objects in type_support_record.items()])

def superclasses(item_list):
    return wiki.sparql(superclasses_query.format(
        types=make_value_list([t.split('/')[-1] for t in item_list])))

def types_related_to_entity_list(entities, concept_id, user_id):
    """ takes a list of wikidata item page IDs, retrieves a bunch of statements involving those,
    and extracts the classes of which related items are instances of. """

    # just the concept connector
    linked_types = [lc.linked_type for lc in Concept.objects.get(id=concept_id).linked_concepts.all()]


    res = wiki.sparql(related_types_query.format(entities=make_value_list(entities)))

    # assign related types to properties, under both type and property key
    types = {}
    props = {}
    for i in res:
        var = lambda x:i.get(x,{}).get('value') # this is how wikidata response to sparql look like don't @ me
        # ?item actually means 'type' in this query
        if i.get('p', {}).get('value'):
            record = types.get(var('item'), {})
            record[var('p')] = record.get(var('p'), []) + [var('obj')]
            types[var('item')] = record

            #record = props.get(var('p'), {})
            #record[var('item')] = record.get(var('item'), []) + [var('obj')]
            props[var('p')] = props.get(var('p'), []) + [var('item')]
        #TODO inverse property ?pr unter `related` eintragen?


    # query supertypes of detected related types
    res = superclasses(types.keys())

    # assign supertypes to  types as well
    for i in res:
        var = lambda x:i[x]['value'] # this is how wikidata response to sparql look like don't @ me
        record = types.get(var('supertype'), {})
        p = 'https://www.wikidata.org/wiki/Property:P279'
        record[p] = record.get(p, []) + [var('type')]
        types[var('supertype')] = record

    ret = types
    for t,rec in types.items():
        ret[t]['count'] = count(rec)
    #ret = sorted([(k,v) for k,v in ret.items()], key=count)
    p_count_mean = sum([len(tt) for p,tt in props.items()]) / len(props) if len(props)>0 else 0
    rep = {p:tt for p,tt in props.items() if len(tt)>p_count_mean}

    return {
            "concept_id": concept_id,
            "concept_external": linked_types,
            "user_id": user_id,
            "related_types": ret,
            "related_properties": rep
            }







