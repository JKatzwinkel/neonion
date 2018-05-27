import uuid

from django.db import models
from common.vocab import neonion
from common.mixins import ResourceMixin

from accounts.models import User
from annotationsets.models import ConceptSet, Concept, Property, LinkedConcept, LinkedProperty

class Recommendation(ResourceMixin, models.Model):
    user = models.ForeignKey(User, blank=True, null=True)
    dismissed = models.NullBooleanField(blank=True, null=True, default=False)
    confidence = models.DecimalField(decimal_places=2, max_digits=10, default=0)
    objects = models.Manager

    def __str__(self):
        return '{} ({})'.format(self.label, self.confidence)

    class Meta:
        app_label = "wikidata"
        ordering = ["-confidence"]


class ConceptRecommendation(Recommendation):

    concept = models.ForeignKey(Concept, blank=True, null=True)
    linked_concept = models.ForeignKey(LinkedConcept, blank=False, on_delete=models.CASCADE)

    class_uri = neonion.CONCEPT_RECOMMENDATION




class PropertyRecommendation(Recommendation):

    property = models.ForeignKey(Property, blank=True, null=True)
    linked_property = models.ForeignKey(LinkedProperty, blank=False, on_delete=models.CASCADE)

    domain = models.ManyToManyField(LinkedConcept, blank=False, related_name='property_recommendation_from')
    range = models.ManyToManyField(LinkedConcept, blank=True, related_name='property_recommendation_to')

    class_uri = neonion.PROPERTY_RECOMMENDATION


