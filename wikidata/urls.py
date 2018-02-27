from django.conf.urls import url, include
from rest_framework import routers

from wikidata.rest import ConceptRecommendationViewSet

import api.urls

router = routers.DefaultRouter(trailing_slash=False)
router.register(r'recommendedconcepts', ConceptRecommendationViewSet)


urlpatterns = [
        url(r'^', include(router.urls)),

        url(r'^itemsearch/(?P<index>.*)/(?P<concept_id>.*)/(?P<term>.*)$', 'wikidata.views.search_typed_items'),
        url(r'^entities/doc/(?P<document_pk>.+)/concept/(?P<concept_id>.*)$', 'wikidata.views.linked_entities_in_document'),
        url(r'^entities/doc/(?P<document_pk>.+)/?$', 'wikidata.views.linked_entities_in_document'),
        url(r'^related/types/doc/(?P<document_pk>.+)/concept/(?P<concept_id>.*)$', 'wikidata.views.types_related_to_entities_in_document'),
        url(r'^statements/doc/(?P<document_pk>.+)/linked/?$', 'wikidata.views.annotated_statements'),
        url(r'^statements/doc/(?P<document_pk>.+)/implicit/?$', 'wikidata.views.implicit_statements'),

        url(r'^entities/label/(?P<item_id>.+)/?$', 'wikidata.views.resolve_item_labels')

        ]

