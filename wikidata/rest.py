from rest_framework import viewsets, status, serializers

from wikidata.models import ConceptRecommendation


class ConceptRecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConceptRecommendation
        fields = ('id', 'label', 'comment', 'concept', 'linked_concept', 'dismissed', 'confidence')

class ConceptRecommendationViewSet(viewsets.ModelViewSet):
    queryset = ConceptRecommendation.objects.all()
    serializer_class = ConceptRecommendationSerializer



