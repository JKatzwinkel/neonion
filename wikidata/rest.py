from rest_framework import viewsets, status, serializers

from wikidata.models import ConceptRecommendation, ReasonForRecommendation, PropertyRecommendation


class ConceptRecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConceptRecommendation
        fields = ('id', 'label', 'comment', 'concept', 'linked_concept', 'dismissed', 'confidence')

class ConceptRecommendationViewSet(viewsets.ModelViewSet):
    queryset = ConceptRecommendation.objects.all()
    serializer_class = ConceptRecommendationSerializer



class PropertyRecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyRecommendation
        fields = ('id', 'label', 'comment', 'domain', 'range', 'property', 'linked_property', 'dismissed', 'confidence')

class PropertyRecommendationViewSet(viewsets.ModelViewSet):
    queryset = PropertyRecommendation.objects.all()
    serializer_class = PropertyRecommendationSerializer



class ReasonForRecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReasonForRecommendation
        fields = ('id', 'label','comment')

class ReasonForRecommendationViewSet(viewsets.ModelViewSet):
    queryset = ReasonForRecommendation.objects.all()
    serializer_class = ReasonForRecommendationSerializer


