from django.conf.urls import url, include
from rest_framework import routers
from viewsets import UserViewSet, WorkingGroupViewSet, DocumentViewSet, ConceptSetViewSet, ConceptViewSet, \
    PropertyViewSet, LinkedConceptViewSet, MembershipViewSet, LinkedPropertyViewSet

# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter(trailing_slash=False)
router.register(r'users', UserViewSet)
router.register(r'memberships', MembershipViewSet)
router.register(r'groups', WorkingGroupViewSet)
router.register(r'documents', DocumentViewSet)
router.register(r'conceptsets', ConceptSetViewSet)
router.register(r'concepts', ConceptViewSet)
router.register(r'linkedconcepts', LinkedConceptViewSet)
router.register(r'properties', PropertyViewSet)
router.register(r'linkedproperties', LinkedPropertyViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),

    # ElasticSearch proxy
    url(r'^es/search/(?P<index>.+)/(?P<type>.+)/(?P<term>.+)$', 'api.views.entity_search'),
    url(r'^es/import/(?P<index>.+)/(?P<type>.+)$', 'api.views.entity_bulk_import'),

    # wikidata remote search
    url(r'^wikidata/search/(?P<type>.+)/(?P<term>.+)$', 'api.views.entity_lookup'),
    url(r'^wikidata/statement/(?P<sid>.+)/(?P<pid>.+)$', 'api.views.predicate_lookup'),
    url(r'^wikidata/recommend/entity/(?P<sid>.+)$', 'api.views.recommend_entity_obj_types'),
    url(r'^wikidata/recommend/properties/(?P<properties_separated_by_semicolon>.+)$', 'api.views.recommend_properties_properties')
]
