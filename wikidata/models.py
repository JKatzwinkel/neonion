from django.db import models
from common.vocab import neonion
from common.mixins import ResourceMixin

from accounts.models import User
from annotationsets.models import ConceptSet, Concept, Property, LinkedConcept, LinkedProperty

class ConceptRecommendation(ResourceMixin, models.Model):

    user = models.ForeignKey(User, blank=True, null=True)

    concept = models.ForeignKey(Concept, blank=True, null=True, on_delete=models.SET_NULL)
    linked_concept = models.ForeignKey(LinkedConcept, blank=False, on_delete=models.CASCADE)

    rejected = models.NullBooleanField(null=True, default=False)

    confidence = models.DecimalField(decimal_places=2, max_digits=3)

    class_uri = neonion.CONCEPT_RECOMMENDATION

    class Meta:
        app_label = "wikidata"


