import json
import uuid

from annotationsets.models import Concept, LinkedConcept
from wikidata.models import ConceptRecommendation, PropertyRecommendation, ReasonForRecommendation

class BasicRecommender:

    def __init__(self, data):
        self.data = data

    def concepts(self):
        pass


    def properties(self):
        pass


def heute_abend_wird_ehrenlos(data):
    """ so ehrenlos! """

    types = data.get('related_types')
    classifier_id = data.get('concept_id')

    # sortieren und filtern, die mit zu wenig statements fliegen raus
    ranked = sorted([(type_item_url,support_record) for type_item_url, support_record in types.items()
        if support_record.get('count',0) > 3],
            key=lambda t:t[1].get('count'),
            reverse=True)

    # los gehts aber wir schmeiszen nochmal die haelfte weg sonst kommt echt viel muell auch
    for type_item_url, support_record in ranked[:len(ranked)/2]:
        type_item_id = type_item_url.split('/')[-1]

        # ok guck ob es schon linked concept fuer das gibt
        try:
            linked_concept = LinkedConcept.objects.get(
                    linked_type__endswith=type_item_id)
        except LinkedConcept.DoesNotExist:
            # einfach erzeugen das ding 1fach mal aus scheisz
            linked_concept = LinkedConcept.objects.create(
                    linked_type=type_item_url,
                    id=uuid.uuid1().hex)

        # ok jetzt wo wir das linked concept schonmal in der hand halten, koennen wir auch gleich paar subclass of beziehungen drunterwemmsen
        subclasses = support_record.get('https://www.wikidata.org/wiki/Property:P279',[]) #TODO
        for subclass_url in subclasses:
            try:
                sub = LinkedConcept.objects.get(linked_type=subclass_url)
                if len(sub.super_types.filter(id=linked_concept.id)) < 1:
                    sub.super_types.add(linked_concept)
                #TODO umgekehrt waere auch geil, aso bei der eigenen superklasse sich drunter haengen aber schonmal besser als nichts
            except:
                pass

        # egal man einfach schonmal abspeichern
        linked_concept.save()

        # ok das haetten wir aber jetzt wird aufregend
        try:
            concept_recommendation = ConceptRecommendation.objects.get(
                    linked_concept_id=linked_concept.id)#XXX unique constraint failed
        except ConceptRecommendation.DoesNotExist:
            # wir legen einfach so ein objekt an als waere es nichts hahaha!
            concept_recommendation = ConceptRecommendation.objects.create(
                    id=uuid.uuid1().hex,
                    linked_concept=linked_concept,
                    user_id=support_record.get('user_id'))#TODO das musz man anders machen



        # jetzt paar geile hard facts da rein schlaumeiern
        #TODO
        # mit begruendung sogar
        reason = ReasonForRecommendation.objects.create(
                label='Closely related to annoted entities of type {}.'.format(classifier_id))
        concept_recommendation.reasons.add(reason)
        concept_recommendation.confidence=support_record.get('count')


        # dann speichern
        concept_recommendation.save()














