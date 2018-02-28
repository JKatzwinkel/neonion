# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('annotationsets', '0002_linkedconcept_super_types'),
        ('wikidata', '0002_auto_20180226_0517'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='recommendation',
            options={'ordering': ['-confidence']},
        ),
        migrations.AddField(
            model_name='propertyrecommendation',
            name='domain',
            field=models.ManyToManyField(related_name='property_recommendation_from', to='annotationsets.LinkedConcept'),
        ),
        migrations.AddField(
            model_name='propertyrecommendation',
            name='range',
            field=models.ManyToManyField(related_name='property_recommendation_to', to='annotationsets.LinkedConcept', blank=True),
        ),
    ]
