import datetime
import json
import uuid

from django.conf import settings
from django.http import JsonResponse, HttpResponse
from pyelasticsearch import ElasticSearch, exceptions
from rest_framework import permissions, generics
from rest_framework.decorators import api_view
from rest_framework.views import APIView

import common.annotation as ann
from api.authentication import UnsafeSessionAuthentication
from common.exceptions import InvalidResourceTypeError, InvalidAnnotationError
from common.uri import generate_uri, generate_urn
from common.vocab import neonion, OpenAnnotation
from store.decorators import require_group_permission
from documents.models import Document
from annotationsets.models import Concept, Property
from logging.annotatorLogger import *

from django.shortcuts import get_object_or_404

from common.knowledge import client as wikiclient

es = ElasticSearch(settings.ELASTICSEARCH_URL)
ANNOTATION_TYPE = 'annotation'
PAGE_SIZE = 1000


def convert_es_to_list(result_set):
    result_set = map(lambda item: item['_source'], result_set['hits']['hits'])
    return {
        'total': len(result_set),
        'rows': result_set
    }

def convert_es_to_dict(result_set):
    result_set = {item['_source']['oa']['@id']:item['_source'] for item in result_set['hits']['hits']}
    return {
        'total': len(result_set),
        'dict': result_set
    }


def empty_result():
    return {'total': 0, 'rows': []}


def get_filter_query(parameters):
    query_params = []
    for key, value in parameters.iteritems():
        query_params.append({
            'term': {key: value}
        })

    return {
        "query": {
          "bool": {
            "must": {"match_all": {}},
            "filter": query_params
            }
          }
        }


class AnnotationListView(APIView):
    # TODO: find solution for annotator.store plugin an CSRF Tokens othern than ignoring the absence of the token
    authentication_classes = (UnsafeSessionAuthentication,)
    permission_classes = (permissions.AllowAny,)

    @require_group_permission
    def get(self, request, group_pk, document_pk, format=None):
        # return empty list on get
        return JsonResponse(empty_result())

    @require_group_permission
    def post(self, request, group_pk, document_pk, format=None):
        """Creates a new annotation"""
        annotation = json.loads(request.body)

        try:
            # firstly validate annotation
            validate = ann.AnnotationValidator()
            validate(annotation)
        except (InvalidAnnotationError, InvalidResourceTypeError):
            return HttpResponse(status=400)
        else:
            annotation['id'] = uuid.uuid1().hex
            ann.add_creator(annotation, request.user.email)
            annotation['created'] = datetime.datetime.now().isoformat()
            annotation['updated'] = annotation['created']

            # OA specific enrichment
            if 'oa' in annotation:
                # add context JSON-LD embedding
                annotation['oa']['@context'] = settings.NEONION_BASE_NAMESPACE.rstrip('/') + "/ns/neonion-context.jsonld",
                # generate URI for annotation
                annotation['oa']['@id'] = generate_uri(neonion.ANNOTATION)

                # enrich body
                if 'hasBody' in annotation['oa']:
                    # generate URN for body
                    annotation['oa']['hasBody']['@id'] = generate_urn()

                    # generate URI for classified or identified instance
                    if (ann.motivation_equals(annotation, OpenAnnotation.Motivations.identifying) or
                        ann.motivation_equals(annotation, OpenAnnotation.Motivations.classifying)):
                        ann.add_resource_uri(annotation)

                # enrich target
                if 'hasTarget' in annotation['oa']:
                    # generate URN for target
                    annotation['oa']['hasTarget']['@id'] = generate_urn()

                    if 'hasSource' in annotation['oa']['hasTarget']:
                        document = Document.objects.get(pk=document_pk)
                        annotation['oa']['hasTarget']['hasSource']['@id'] = document.uri()

                    if 'hasSelector' in annotation['oa']['hasTarget']:
                        # generate URN for selector
                        annotation['oa']['hasTarget']['hasSelector']['@id'] = generate_urn()

            # Annotator specific enrichment
            # add permissions
            annotation['permissions'] = {
                'read': [group_pk],
                'update': [group_pk],
                'delete': [request.user.email],
                'admin': [request.user.email]
            }

            # serialize annotation to triple store
            if hasattr(settings, 'ENDPOINT_ENABLED') and settings.ENDPOINT_ENABLED:
                try:
                    ann.endpoint_create_annotation(annotation)
                except Exception:
                    pass

            try:
                es.index(settings.ELASTICSEARCH_INDEX, ANNOTATION_TYPE, annotation, id=annotation['id'])
		log_annotation_created(request)
            except:
                return HttpResponse(status=500)
            else:
                return JsonResponse(annotation, status=201, safe=False)


class AnnotationDetailView(APIView):
    # TODO: find solution for annotator.store plugin an CSRF Tokens other than ignoring the absence of the token
    authentication_classes = (UnsafeSessionAuthentication,)
    permission_classes = (permissions.AllowAny,)

    @require_group_permission
    def get(self, request, group_pk, document_pk, annotation_pk, format=None):
        """Returns the specified annotation object"""
        try:
            annotation = es.get(settings.ELASTICSEARCH_INDEX, ANNOTATION_TYPE, annotation_pk)
        except:
            return HttpResponse(status=500)
        else:
            return JsonResponse(annotation, safe=False)

    @require_group_permission
    def put(self, request, group_pk, document_pk, annotation_pk, format=None):
        """Updates the specified annotation object"""
        annotation = json.loads(request.body)

        try:
            # firstly validate annotation
            validate = ann.AnnotationValidator()
            validate(annotation)
        except (InvalidAnnotationError, InvalidResourceTypeError):
            return HttpResponse(status=400)
        else:
            ann.add_creator(annotation, request.user.email)
            annotation['updated'] = datetime.datetime.now().isoformat()

            try:
                es.index(settings.ELASTICSEARCH_INDEX, ANNOTATION_TYPE, annotation,
                         id=annotation['id'], overwrite_existing=True)
		log_annotation_edited(request)
            except:
                return HttpResponse(status=500)
            else:
                return JsonResponse(annotation, status=200, safe=False)

    @require_group_permission
    def delete(self, request, group_pk, document_pk, annotation_pk, format=None):
        """Deletes the specified annotation object"""
        try:
            es.delete(settings.ELASTICSEARCH_INDEX, ANNOTATION_TYPE, annotation_pk)
            log_annotation_deleted(request)
        except:
            return HttpResponse(status=500)
        else:
            return HttpResponse(status=204)


class SearchView(generics.GenericAPIView):

    @require_group_permission
    def get(self, request, group_pk, document_pk, format=None):
        params = dict(request.GET)
        offset = params.pop("offset", 0)
        size = params.pop("limit", PAGE_SIZE)
        params['permissions.read'] = group_pk
        params['uri'] = document_pk

        try:
            query = get_filter_query(params)
            response = es.search(query, index=settings.ELASTICSEARCH_INDEX,
                                 doc_type=ANNOTATION_TYPE, es_from=offset, size=size)
        except exceptions.ElasticHttpNotFoundError:
            return JsonResponse(empty_result())
        except:
            return HttpResponse(status=500)
        else:
            return JsonResponse(convert_es_to_list(response), safe=False)




def retrieve(request, group_pk, document_pk):
    params = dict(request.GET)
    offset = params.pop("offset", 0)
    size = params.pop("limit", PAGE_SIZE)
    params['permissions.read'] = group_pk
    params['uri'] = document_pk
    #params['oa.motivatedBy'] = 'oa:linking'
    print(params)

    try:
        query = get_filter_query(params)
        response = es.search(query, index=settings.ELASTICSEARCH_INDEX,
                             doc_type=ANNOTATION_TYPE, es_from=offset, size=size)
        res = convert_es_to_dict(response)
        print('results: ', len(res['dict']))
        return res
    except:
        return None


class StatementListView(APIView):

    @require_group_permission
    def get(self, request, group_pk, document_pk):
        try:
            results = retrieve(request, group_pk, document_pk)

            predicates = [anno for anno in results['dict'].values() if anno['oa']['motivatedBy'] == 'oa:linking']

            statements = [{
                "subject": results['dict'].get(anno['oa']['hasTarget']['hasSelector']['source']),
                "property": anno,
                "object": results['dict'].get(anno['oa']['hasTarget']['hasSelector']['target'])
            } for anno in predicates]

        except exceptions.ElasticHttpNotFoundError:
            return JsonResponse(empty_result())
        except:
            return HttpResponse(status=500)
        else:
            return JsonResponse(statements, safe=False)


def resolve_linked_concepts(classifiedAs):
    concept_id = classifiedAs.split('/')[-1]
    concept = get_object_or_404(Concept, pk=concept_id)
    return [linked_concept.linked_type.split('/')[-1] for linked_concept in concept.linked_concepts.all()]

def resolve_linked_property(relation):
    prop_pk = relation.split('/')[-1]
    prop = get_object_or_404(Property, pk=prop_pk)
    return [linked_prop.linked_property.split(':')[-1] for linked_prop in prop.linked_properties.all()]


class GroupedStatementsView(APIView):

    @require_group_permission
    def get(self, request, group_pk, document_pk):
        try:
            results = retrieve(request, group_pk, document_pk)

            entities = [anno for anno in results['dict'].values() if anno['oa']['motivatedBy'] in ['oa:identifying', 'oa:classifying']]
            predicates = [anno for anno in results['dict'].values() if anno['oa']['motivatedBy'] == 'oa:linking']

            # this os going to be some kind of tiny wikidata build from this document's annotations
            statements = {}
            # this is a registry of wikidata itempage ids found in annotations
            itempages = {}

            # collect is_a (P31) predicates
            for item in entities:
                body = item['oa']['hasBody']
                item_id = body.get('identifiedAs').split('/')[-1] if 'identifiedAs' in body else item['oa']['@id']
                itempage = statements.get(item_id, {})
                if 'identifiedAs' in body:
                    itempage['item_page'] = item_id
                    # register itempage id
                    itempages[item['oa']['@id']] = item_id

                itempage['aliases'] = itempage.get('aliases', []) + [item.get('quote') or body.get('label', '')]

                properties = itempage.get('properties', {})
                for item_type in resolve_linked_concepts(body.get('classifiedAs', '')):
                    properties['P31'] = properties.get('P31', {})
                    properties['P31'][item_type] = {}

                itempage['properties'] = {p:{x:{} for x in set(o)} for p,o in properties.items()}

                statements[item_id] = itempage

            # process actual statements (triples, 2 annotations connected by property)
            for pred in predicates:
                item_id = pred['oa']['hasTarget']['hasSelector']['source']
                obj_id = pred['oa']['hasTarget']['hasSelector']['target']
                # switch annotation identifier with itempage id if necessary
                item_id = itempages.get(item_id, item_id)
                obj_id = itempages.get(obj_id, obj_id)
                itempage = statements.get(item_id)
                item_properties = itempage.get('properties', {})

                property = pred['oa']['hasBody']['relation']
                for link_prop_id in resolve_linked_property(property):
                    item_properties[link_prop_id] = item_properties.get(link_prop_id, {})
                    item_properties[link_prop_id][obj_id] = {}

                itempage['properties'] = {p:{x:{} for x in set(o)} for p,o in item_properties.items()}
                statements[item_id] = itempage

            # use wikidata itempage of this document
            doc = get_object_or_404(Document, pk=document_pk)
            if doc.url and wikiclient.is_itempage_url(doc.url):
                item_id = doc.url.split('/')[-1]
                item_id = itempages.get(item_id, item_id)
                itempage = statements.get(item_id, {})
                itempage['item_page'] = item_id

                properties = itempage.get('properties', {})
                # technically, all annotated entities could be key subjects to this article
                for item in entities:
                    properties['P921'] = properties.get('P921', {})
                    properties['P921'][itempages.get(item['oa']['@id'])] = {}

                itempage['properties'] = {p:{x:{} for x in set(o)} for p,o in properties.items()}
                statements[item_id] = itempage



        except exceptions.ElasticHttpNotFoundError:
            return JsonResponse(empty_result())
        except Exception as e:
            print('shit!')
            print(e.message)
            return HttpResponse(status=500)
        else:
            return JsonResponse(statements, safe=False)



@api_view(["GET"])
def root(request):
    return JsonResponse([], safe=False)


@api_view(["GET"])
def search(request, format=None):
    params = dict(request.GET)
    offset = params.pop("offset", 0)
    size = params.pop("limit", PAGE_SIZE)

    try:
        query = get_filter_query(params)
        response = es.search(query, index=settings.ELASTICSEARCH_INDEX,
                             doc_type=ANNOTATION_TYPE, es_from=offset, size=size)
    except exceptions.ElasticHttpNotFoundError:
        return JsonResponse(empty_result())
    except:
        return HttpResponse(status=500)
    else:
        return JsonResponse(convert_es_to_list(response), safe=False)
