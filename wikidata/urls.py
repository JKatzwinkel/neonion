from django.conf.urls import url


urlpatterns = [
        url(r'^itemsearch/(?P<index>.*)/(?P<concept_id>.*)/(?P<term>.*)$', 'wikidata.views.search_typed_items'),
        url(r'^statements/doc/(?P<document_pk>.+)/linked/?$', 'wikidata.views.annotated_statements'),
        url(r'^statements/doc/(?P<document_pk>.+)/implicit/?$', 'wikidata.views.implicit_statements')
        ]
