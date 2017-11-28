import logging

import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from pyelasticsearch import ElasticSearch, bulk_chunks
from pyelasticsearch.exceptions import IndexAlreadyExistsError, BulkError, ElasticHttpError, ElasticHttpNotFoundError

from common.knowledge.provider import Provider
from common.knowledge.client import WikidataClient, snoopy_request
from common.knowledge.testrecommender import TestRecommender, SimpleRecommender


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

@login_required
@require_POST
def entity_bulk_import(request, index, type):
    json_data = ''
    # read chunks
    f = request.FILES.getlist('file')[0]
    for chunk in f.chunks():
        json_data += chunk

    data = json.loads(json_data)

    es = ElasticSearch(settings.ELASTICSEARCH_URL)
    try:
        es.create_index(index)
    except IndexAlreadyExistsError:
        pass
    except ElasticHttpError:
        pass

    # clear item of type in document
    try:
        es.delete_all(index, type)
    except (ElasticHttpError, ElasticHttpNotFoundError):
        pass

    # create generator
    def items():
        for item in data:
            yield es.index_op(item)

    for chunk in bulk_chunks(items(), docs_per_chunk=500, bytes_per_chunk=10000):
        try:
            es.bulk(chunk, doc_type=type, index=index)
        except BulkError:
            pass

    # refresh the index
    es.refresh(index)

    return HttpResponse(status=201)


@login_required
@require_GET
def entity_search(request, index, type, term):
    # call search method from provider
    provider = Provider(settings.ELASTICSEARCH_URL)
    return JsonResponse(provider.search(term, type, index), safe=False)

@login_required
@require_GET
def entity_lookup(request, type, term):
    logger.info(u'supposed to lookup up "{}" ({})'.format(term, type))
    result = wikidataClient.search(term, type)
    logger.info(result)
    return JsonResponse(result,safe=False)

@require_GET
def predicate_lookup(request, sid, pid):
    #wikidataClient = WikidataClient()
    result = wikidataClient.sparql('wd:{} wdt:{} ?o'.format(sid, pid))
    result = [o.get('o', {}) for o in result]
    result = [o.get('value', '') for o in result if o.get('type') == 'uri']
    result = [u.split('/')[-1] for u in result]
    return JsonResponse({
        "subject": sid,
        "property": pid,
        "objects":result}, safe=False)

@require_GET
def recommend_entity_obj_types(request, cid, sid):
    recommender = SimpleRecommender()
    result = recommender.entity_rec(cid, sid)
    return JsonResponse(result)

@require_GET
def recommend_properties_properties(request, properties_separated_by_semicolon):
    properties = properties_separated_by_semicolon.split(';')
    # TODO validate arguments
    data = json.loads(snoopy_request(properties))
    return JsonResponse(data)

@require_GET
def recommend_linked_concepts(request):
    recommender = SimpleRecommender()
    result = recommender.linked_concepts()
    return JsonResponse(result)

@require_GET
def recommend_linked_properties(request):
    recommender = SimpleRecommender()
    result = recommender.linked_properties()
    return JsonResponse(result)


@require_GET
def recommend(request):
    recommender = SimpleRecommender()
    recommendations = recommender.recommend()
    return JsonResponse(recommendations)


## wikidata/reference endpoint, look up or create source reference for statement
def statement_reference(request, sid, pid, oid, document_url):
    document_id = wikidataClient.extract_id(document_url)
    print(document_id)
    if request.method == "GET":
        res = wikidataClient.find_claim_source(sid, pid, oid, document_id)
        return JsonResponse(res)
    elif request.method == "POST":
        res = wikidataClient.support_claim(sid, pid, oid, document_id)
        print(res)
        return JsonResponse(res)
    return JsonResponse({})


wikidataClient = WikidataClient()
