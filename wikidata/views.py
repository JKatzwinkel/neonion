import os
import re
import json
import requests
from urllib import urlencode

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.core import serializers

from annotationsets.models import Concept, LinkedConcept, Property, LinkedProperty
import store

os.environ["PYWIKIBOT2_NO_USER_CONFIG"] = "1"

import wiki
import util
import recommender



# action, search, limit
wbapi_url_template = "https://www.wikidata.org/w/api.php?format=json&{}"

# insert 2 lists of items: instances and types to match against
types_query_template = 'VALUES ?item {{{}}} . VALUES ?type {{{}}} . ?item wdt:P31/wdt:P279* ?type.'

# insert filtered list of items
birth_death_query_template = 'VALUES ?item {{{}}} . {}'

# regular expression for parsing wikidata xs:dateTime literals
rx_dateTime = re.compile('^([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-2][0-9]:[0-5][0-9]:[0-5][0-9]).*$')

# when querying for additional information to render into search result list, we look for these properties
temporal_properties = {
        "birth": "P569",
        "death": "P570"
        }


# render QId list to string with wd: prefix for every ID and space as delimiter
# (can be used for sparql expression ' VALUES ?item {...} . '
wd_item_id_list = lambda qids: ' '.join(['wd:' + qid for qid in qids])
# prepare query components for temporal_properties defined above
wd_opt_props = ' . '.join(
        ['OPTIONAL {{ ?item wdt:{} ?{} }}'.format(v, k)
            for k, v in temporal_properties.items()])

# TODO determine lang parameter based on language of document
def wbsearchentities(terms, limit=50, lang='en'):
    """Queries Wikidata's Wikibase API endpoint with action wbsearchentities"""
    res = []
    if terms and len(terms) > 0:
        url = wbapi_url_template.format(urlencode({
            "action": "wbsearchentities",
            "search": unicode(terms).encode('utf-8'),
            "limit": limit,
            "language": lang,
            "uselang": lang
            }))
        response = requests.get(url)
        if response.status_code == 200:
            for i, result in enumerate(response.json().get('search', [])):
                res.append(result)
                result['rank'] = i
    return res

def validate_item_types(results, concept):
    """Takes an id:search_result dict and flags all items that match a linked concept of the passed neonion concept."""
    # extract Q-ids from URLs of external types linked to concept
    concept_linked_types_qids = [lc.linked_type.split('/')[-1] for lc in concept.linked_concepts.all()]
    # fill in item and type lists in SPARQL query
    query = types_query_template.format(
            wd_item_id_list(results.keys()),
            wd_item_id_list(concept_linked_types_qids)
            )
    # query WDQS endpoint, retrieve pywikidata ItemPage objects
    items = wiki.query(query)
    # in the search result dictionary, flag all items that are amongst results of previous SPARQL query
    for item in items:
        results[item.id]['valid'] = True
    # return
    return results


def add_temporal_data(results):
    """Try to retrieve timespan information like dates of birth and death."""
    # insert item IDs into SPARQL query template (only items of valid type for classifying concept)
    # insert OPTIONAL clauses matching properties defined above (temporal_properties)
    query = birth_death_query_template.format(
                wd_item_id_list(
                    [k for k,v in results.items() if v.get('valid')]
                    ),
                wd_opt_props
            )
    # query WDQS endpoint and retrieve JSON
    data = wiki.sparql(query)
    # TODO problem is that in order to do this properly, we would need to resolve predicate qualifiers because otherwise we
    # TODO can't tell whether a date is of the Gregorian or Julian calendar, nor what is its granularity/precision.
    # TODO this means we would specify the temporal properties not with wdt: but with p: prefix (which will return a statement url rather than a dateTime literal as value)
    # TODO and somehow address the statement's properties in the query. that's ridiculously complicated so we don't do it for now.
    # process response
    for row in data:
        # get corresponding entry in results dictionary (key: wd url hindmost segment of path)
        item = results.get(row.get('item', {}).get('value', '').split('/')[-1])
        # parse values for specified properties
        for prop in temporal_properties.keys():
            predicate = row.get(prop, {})
            if predicate.get('datatype') == 'http://www.w3.org/2001/XMLSchema#dateTime' and predicate.get('type') == 'literal':
                values = rx_dateTime.findall(predicate.get('value', ''))
                if len(values) > 0:
                    # if value available, write into dictionary
                    item[prop] = values[0][0]
    return results



# key mapping from wikidata to neonion (annotator controller)
mappings = {
        "description" : "descr",
        "concepturi": "uri",
        "repository": None,
        "title": None,
        "match": None
        }

def map_result(item):
    for wd_key, key in mappings.items():
        if key:
            item[key] = item.get(wd_key)
        if wd_key in item:
            del item[wd_key]
    return item



def get_value(obj, path):
    """ retrieve value of a field within an object addressed by a colon-delimited path. """
    keys = path.split(':')
    while len(keys) > 0:
        key = keys.pop(0)
        obj = obj.get(key, {})
    return obj


###########################################################################################################
##                                              VIEWS                                                    ##
###########################################################################################################

def search_typed_items(request, index, concept_id, term):

    item_list = []

    # go search for entities with matching labels/aliases
    results = wbsearchentities(term)
    # convert result list to dictionary, use ids as keys
    results = {result['id']:result for result in results}

    # retrieve neonion concept used for classification of selected terms
    concept = Concept.objects.get(id=concept_id)
    results = validate_item_types(results, concept)

    # try to enhance search results with life span information for persons
    # TODO add temporal data extraction and formatting for other concepts as well
    if concept_id == 'person':
        results = add_temporal_data(results)

    # return only matching items of valid type, mapped into schema expected by annotator controller and sorted by original rank
    item_list = filter(lambda r:r.get('valid'),
            map(map_result,
                sorted(results.values(),
                    key=lambda r:r.get('rank',-1))))

    return JsonResponse(item_list, safe=False)


def linked_entities_in_document(request, document_pk, concept_id=None, as_view=True):
    """ retrieve IDs of linked resources from elasticsearch annotations store """
    entity_list = store.views.annotated_entities(dict(request.GET), document_pk, concept_id)
    if concept_id:
        entities = [get_value(entity, 'identifiedAs') for entity in entity_list if get_value(entity, 'classifiedAs').endswith(concept_id)]
    else:
        entities = [get_value(entity, 'identifiedAs') for entity in entity_list]
    return JsonResponse(entities, safe=False) if as_view else entities


def types_related_to_entities_in_document(request, document_pk, concept_id=None):
    """ extract terminological knowledge from collection of entities specified by a document and the concept which was used to annotate them there. """
    entities = linked_entities_in_document(request, document_pk,
            concept_id, as_view=False)
    entities = [e.split('/')[-1] for e in entities]
    types = util.types_related_to_entity_list(entities, concept_id, request.user.id)

    if request.method == 'PUT':
        recommender.heute_abend_wird_ehrenlos(types)


    return JsonResponse(types, safe=False)


def annotated_statements_as_json(params, document_pk):
    # retrieve oa annotations from elasticsearch store
    all_annotations = store.views.linked_annotations(params, document_pk)

    statements = []
    for anno in all_annotations.values():
        if anno.get('oa',{}).get('motivatedBy') == 'oa:linking':

            statement = {}

            prop_id = get_value(anno, "oa:hasBody:relation")
            # resolve linked properties
            prop = get_object_or_404(Property, pk=prop_id.split('/')[-1])

            statement['property'] = {
                    'id': prop_id,
                    'linked': [linked_property.linked_property for linked_property in prop.linked_properties.all()]
                    }

            # resolve object linked to subject and object annotation
            for entity_role, oa_path in [('subject',"oa:hasTarget:hasSelector:source"), ('object', "oa:hasTarget:hasSelector:target")]:

                entity_anno_id = get_value(anno, oa_path)

                entity_anno = all_annotations.get(entity_anno_id)
                concept_id = get_value(entity_anno, "oa:hasBody:classifiedAs")
                concept = get_object_or_404(Concept, pk=concept_id.split('/')[-1])

                statement[entity_role] = {
                        'label': get_value(entity_anno, "oa:hasBody:label"),
                        'internal': get_value(entity_anno, "oa:hasBody:contextualizedAs"),
                        'id': get_value(entity_anno, "oa:hasBody:identifiedAs"),
                        'concept': {
                            'id': concept_id,
                            'linked': [linked_concept.linked_type for linked_concept in concept.linked_concepts.all()]
                            }
                        }

            statements.append(statement)

    return statements


def resolve_item_labels(request, item_id):
    params = dict(request.GET)
    wdid = wiki.extract_id(item_id)
    item = wiki.item(item_id) if wdid.startswith('Q') else wiki.prop(item_id)
    return JsonResponse({
        'label': wiki.label(item) or "",
        'description': wiki.description(item) or ""
        })


def accept_concept_recommendation(request, recommendation_id, conceptset_id):
    params = dict(request.GET)
    concept = recommender.accept_concept(recommendation_id, conceptset_id)
    return JsonResponse(serializers.serialize('json', [concept]), safe=False)


#TODO uncomment, add group_pk
#@require_group_permission
@require_GET
def annotated_statements(request, document_pk):
    params = dict(request.GET)
    statements = annotated_statements_as_json(params, document_pk)
    return JsonResponse(statements, safe=False)

def implicit_statements(request, document_pk):
    params = dict(request.GET)
    raise NotImplementedError('view is not implemented yet')

