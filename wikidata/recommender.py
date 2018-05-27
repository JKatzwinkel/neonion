import json
import uuid
from datetime import datetime
from math import log

from annotationsets.models import ConceptSet, Concept, LinkedConcept, LinkedProperty, Property
from wikidata.models import ConceptRecommendation, PropertyRecommendation
from wikidata import wiki, util, terminology


_recommender_registry = {
        "concept": [],
        "property": []
        }

def recommender(kind):
    def recommender_decorator(func):
        def wrapper():
            func()
        _recommender_registry.get(kind, []).append({
            'func': wrapper,
            'kind': kind,
            'desc': func.__doc__,
            'name': func.__name__})
        wrapper.__name__ = func.__name__
        return wrapper
    return recommender_decorator


@recommender("concept")
def recommend_common_supertypes():
    """ a simple page rank implementation. """
    print('running supertype recommender')
    count = terminology.count_object_types('apparatus')
    scores = terminology.pagerank('apparatus', count)
    taxonomy = {}
    for term in scores.keys():
        term_data = terminology.lookup_term_record('apparatus', 'term', term)
        taxonomy[term] = {k:term_data.get(k, []) for k in ['broader', 'narrower']}
    threshold = max(scores.values()) * .25
    candidates = {term:scores.get(term) for term in taxonomy.keys()
            if len(taxonomy.get(term,{}).get('broader',[])) < 1
            and scores.get(term,0) > threshold}
    for term, score in candidates.items():
        print(u'{} ({}) - {}  ({})'.format(wiki.label(term), term, score, count.get(term,0)))
    return candidates


@recommender("property")
def most_frequent_properties():
    """ determined the properties that occur most. """
    print('running property recommender')
    properties = terminology.faceted_statements('apparatus', 'pt', query='NOT t:null')
    ranking = sorted(properties.items(), key=lambda t:len(t[1]))[len(properties)/2:]

    for term,info in ranking:
        objects = []
        for tt,objs in info.items():
            objects.extend([o.get('o') for o in objs])
        objects = set(objects)
        print(u'{} ({}) types: {} individual objects: {} ratio {}'.format(wiki.label(term), term, len(info), len(objects), 1.*len(objects)/len(info)))

    return {term:len(info) for term,info in ranking}


candidates = {}
def doit():
    global candidates
    for kind, registered in _recommender_registry.items():
        print(kind)
        for rec in registered:
            print(rec)
            cand = rec.get('func')()
            if cand:
                for term,score in cand.items():
                    candidates[kind] = candidates.get(kind, []) + [{
                        'score': score,
                        'term': term,
                        'provider': rec.get('name'),
                        'description': rec.get('desc')}]







def normalize(data):
    types = data.get('related_types')
    props = data.get('related_properties')

    for type_item_url, support_record in types.items():
        weight = 0
        for purl, objects in support_record.get('predicates',{}).items():
            try:
                wiki.extract_id(purl)
                tf = len(objects)
                df = props.get(purl,{}).get('count')
                if df > 0:
                    idf = log(1. * len(types) / df)
                    tfidf = tf * idf
                    weight += tfidf
            except:
                pass
        support_record['weight'] = support_record.get('weight', 0) + weight
    return data



def make_concept_recommendation_if_necessary(type_item_id, linked_concept, classifier_id, support_record):
    # nur wenn noch kein so ein concept gibt
    # also nur unter folgender bedingung:
    if len(Concept.objects.filter(linked_concepts__linked_type__endswith=type_item_id)) < 1:
        #
        # in diesem fall sollten wir bei bedarf ein conceptrecommendation objekt anlegen, sonst aber nicht
        # weil es gibt das richtige konzept ja schon.
        # wenn es das konzept noch nicht gibt, kann man gucken ob man geeignete conceptrecommendation findet
        # und wenn nicht eine anlegen

        try:
            concept_recommendation = ConceptRecommendation.objects.get(
                    linked_concept_id=linked_concept.id)
        except ConceptRecommendation.DoesNotExist:
            # wir legen einfach so ein objekt an als waere es nichts hahaha!
            concept_recommendation = ConceptRecommendation.objects.create(
                    id=uuid.uuid1().hex,
                    linked_concept=linked_concept,
                    user_id=support_record.get('user_id'))#TODO das musz man anders machen

        # jetzt paar geile hard facts da rein schlaumeiern
        #TODO
        concept_recommendation.label = linked_concept.label if len(linked_concept.label)>0 else ""
        # mit begruendung sogar
        explanation = 'Closely related to annotated entities of type {}.\n'.format(classifier_id)
        if not explanation in concept_recommendation.comment:
            concept_recommendation.comment += explanation
        concept_recommendation.confidence = support_record.get(
                'weight',
                support_record.get('count'))

        # dann speichern
        concept_recommendation.save()
        return concept_recommendation






def get_linked_concept(type_item_url, create=False):
    type_item_id = type_item_url.split('/')[-1]
    linked_concept=None
    # check if any linked concept object containing this type already exists
    try:
        linked_concept = LinkedConcept.objects.get(
                linked_type__endswith=type_item_id)
    except LinkedConcept.DoesNotExist:
        if create:
            # in case type is not yet present in form of a linked concept, create one
            linked_concept = LinkedConcept.objects.create(
                    linked_type=type_item_url,
                    id=uuid.uuid1().hex+type_item_id)
            linked_concept.comment = 'Wikidata class {}'.format(type_item_id)
            linked_concept.retrieved_at = datetime.now()
            linked_concept.endpoint = u'https://www.wikidata.org'
    return linked_concept


def get_linked_property(purl):
    property_id = purl.split('/')[-1]
    try:
        # check if any linked property object containing this property already exists
        linked_property = LinkedProperty.objects.get(
                linked_property__endswith=property_id)
    except LinkedProperty.DoesNotExist:
        # in case property is not yet present in form of a linked concept, create one
        linked_property = LinkedProperty.objects.create(
                linked_property=purl,
                id=uuid.uuid1().hex+property_id,
                comment='Wikidata property {}'.format(property_id))

        linked_property.retrieved_at = datetime.now()
    return linked_property


def accept_concept(recommendation_id, conceptset_id):
    # retrieve conceptset
    conceptset = ConceptSet.objects.get(id=conceptset_id)
    # reify recommendation
    recommendation = ConceptRecommendation.objects.get(id=recommendation_id)
    # retrieve linked concept
    linked_concept = recommendation.linked_concept
    # create concept if there is none (its unlikely that there is)
    if not recommendation.concept:
        wdid = wiki.extract_id(linked_concept.linked_type)
        concept = Concept.objects.create(
                id=wdid,
                label=recommendation.label if len(recommendation.label)>0 else linked_concept.label,
                comment=recommendation.comment)
        concept.linked_concepts.add(linked_concept)
        #TODO properties reinfummeln
        # mit anderen worten wenn ein neues concept erstellt wird, kann es sein, dasz das entsprechende linked concept
        # irgendwann schonmal in 1 property recommendation erwaehnt wurde, aber bei erstellung der property das concept
        # noch nicht da war und deshalb die property nicht anwendbar ist
        # TODO deshalb beim erstellen von concepts bitte bei den dazugehoerigen linked concepts gucken ob diese in
        # property recommendations stehen, und dann das neue concept mit den daraus entstandenen properties ausstatten!
        concept.save()
    conceptset.concepts.add(concept)
    conceptset.save()
    recommendation.dismissed = True
    recommendation.save()
    return concept


def accept_property(recommendation_id, conceptset_id):
    conceptset = ConceptSet.objects.get(id=conceptset_id)
    recommendation = PropertyRecommendation.objects.get(id=recommendation_id)
    linked_property = recommendation.linked_property
    # erstmal property bauen
    # wenn keine da ist
    if len(Property.objects.filter(linked_properties=linked_property)) < 1:
        wdid = wiki.extract_id(linked_property.linked_property)
        prop = Property.objects.create(id=wdid,
                label=recommendation.label if len(recommendation.label)>0 else linked_property.label,
                comment=recommendation.comment)
        prop.linked_properties.add(linked_property)

        # ufff
        #TODO domain
        domain = Concept.objects.filter(linked_concepts__in=recommendation.domain.all())
        for concept in domain:
            concept.properties.add(prop)
            concept.save()
        # range
        prop.range = Concept.objects.filter(linked_concepts__in=recommendation.range.all())
        prop.save()

    recommendation.dismissed = True
    recommendation.save()
    return prop



def compute_recommendations(data):
    """ process predicate/type record assembled from SPARQL queries about locally identified instances of a certain concept. """

    data = normalize(data)

    types = data.get('related_types')
    classifier_id = data.get('concept_id')

    # sortieren und filtern, die mit zu wenig statements fliegen raus
    ranked = sorted([(type_item_url,support_record)
        for type_item_url, support_record in types.items()
        if support_record.get('count',0) > 2],
            key=lambda t:t[1].get('count'),
            reverse=True)

    props = data.get('related_properties')

    # los gehts aber wir schmeiszen nochmal die haelfte weg sonst kommt echt viel muell auch
    for type_item_url, support_record in ranked[:len(ranked)/2]:
        type_item_id = type_item_url.split('/')[-1]

        linked_concept = get_linked_concept(type_item_url, create=True)

        # ok jetzt wo wir das linked concept schonmal in der hand halten, koennen wir auch gleich paar subclass of beziehungen drunterwemmsen
        subclasses = support_record.get('predicates',{}).get('https://www.wikidata.org/prop/direct/P279',[]) #TODO
        for subclass_url in subclasses:
            try:
                sub = LinkedConcept.objects.get(linked_type=subclass_url)
                if len(sub.super_types.filter(id=linked_concept.id)) < 1:
                    sub.super_types.add(linked_concept)
                    sub.save()
                #TODO umgekehrt waere auch geil, aso bei der eigenen superklasse sich drunter haengen aber schonmal besser als nichts
            except:
                pass

        # egal man einfach schonmal abspeichern
        linked_concept.save()

        # ok das haetten wir aber jetzt wird aufregend
        make_concept_recommendation_if_necessary(type_item_id, linked_concept,
                classifier_id, support_record)

    # ok jetzt properties
    # linked concept fuer property domain
    linked_concept_domain = Concept.objects.get(id=classifier_id).linked_concepts.get(
            endpoint__endswith='wikidata.org')

    # geh property liste von http endpunkt durch
    for purl, range_types in props.items():
        range_types = range_types.get('types', [])
        pid = purl.split('/')[-1]
        #props[pid] = props.get(pid, []) + [type_item_id]##XXX


        # gucken ob beide enden der relation bereits als linked concepts vorliegen. sonst sparen wir uns den aufwand
        # also gucken ob irgendwelche der assoziierten wikidata IDs lokal schon als linked concept vorliegen auch
        linked_concept_range = [x for x in
                [get_linked_concept(range_type_url) for range_type_url in range_types]
                if x]
        # gibt es ueberhaupt ein linked concept wo die property rauf zeigen soll?
        if len(linked_concept_range) > 0:
            # linked property holen oder erzeugen
            linked_property = get_linked_property(purl)
            linked_property.save() #???

            #Property.objects.get(linked_properties__linked_property__endswith='P57')
            try:
                property_recommendation = PropertyRecommendation.objects.get(
                        linked_property__linked_property__endswith=pid)
            except PropertyRecommendation.DoesNotExist:
                property_recommendation = PropertyRecommendation.objects.create(
                        id=linked_property.id+'rec',
                        linked_property=linked_property,
                        comment=pid)

            property_recommendation.confidence = len(range_types)
            property_recommendation.domain.add(linked_concept_domain)
            for lc in linked_concept_range:
                property_recommendation.range.add(lc)

            property_recommendation.save()



    # snoopy nun
    concept_properties = [lp.linked_property.split('/')[-1]
            for p in Concept.objects.get(id=classifier_id).properties.all()
            for lp in p.linked_properties.all()]

    print(concept_properties)
    if len(concept_properties) > 0:
        property_suggestions = util.snoopy_property_suggestion(concept_properties).get('recommentations',[])

        for suggestion in property_suggestions:
            pid = suggestion['property']
            lp = get_linked_property("https://www.wikidata.org/wiki/Property:{}".format(pid))

            try:
                property_recommendation = PropertyRecommendation.objects.get(
                        linked_property__linked_property__endswith=pid)
            except PropertyRecommendation.DoesNotExist:
                property_recommendation = PropertyRecommendation.objects.create(
                        id=linked_property.id+'rec',
                        linked_property=linked_property,
                        comment=pid)

            property_recommendation.confidence += suggestion['relevance_measure']
            property_recommendation.save()


















