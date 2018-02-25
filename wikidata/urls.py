from django.conf.urls import url


urlpatterns = [
        url(r'^itemsearch/(?P<index>.*)/(?P<concept_id>.*)/(?P<term>.*)$', 'wikidata.views.search_typed_items'),
        url(r'^entities/doc/(?P<document_pk>.+)/concept/(?P<concept_id>.*)$', 'wikidata.views.linked_entities_in_document'),
        url(r'^entities/doc/(?P<document_pk>.+)/?$', 'wikidata.views.linked_entities_in_document'),
        url(r'^related/types/doc/(?P<document_pk>.+)/concept/(?P<concept_id>.*)$', 'wikidata.views.types_related_to_entities_in_document'),
        url(r'^statements/doc/(?P<document_pk>.+)/linked/?$', 'wikidata.views.annotated_statements'),
        url(r'^statements/doc/(?P<document_pk>.+)/implicit/?$', 'wikidata.views.implicit_statements')
        ]
