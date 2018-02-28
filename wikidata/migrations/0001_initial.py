# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('annotationsets', '0002_linkedconcept_super_types'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReasonForRecommendation',
            fields=[
                ('id', models.CharField(max_length=50, serialize=False, verbose_name=b'id', primary_key=True)),
                ('label', models.CharField(max_length=100, verbose_name=b'label')),
                ('comment', models.CharField(max_length=500, verbose_name=b'comment', blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Recommendation',
            fields=[
                ('id', models.CharField(max_length=50, serialize=False, verbose_name=b'id', primary_key=True)),
                ('label', models.CharField(max_length=100, verbose_name=b'label')),
                ('comment', models.CharField(max_length=500, verbose_name=b'comment', blank=True)),
                ('dismissed', models.NullBooleanField(default=False)),
                ('confidence', models.DecimalField(max_digits=10, decimal_places=2)),
            ],
        ),
        migrations.CreateModel(
            name='ConceptRecommendation',
            fields=[
                ('recommendation_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='wikidata.Recommendation')),
                ('concept', models.ForeignKey(blank=True, to='annotationsets.Concept', null=True)),
                ('linked_concept', models.ForeignKey(to='annotationsets.LinkedConcept')),
            ],
            bases=('wikidata.recommendation', models.Model),
        ),
        migrations.CreateModel(
            name='PropertyRecommendation',
            fields=[
                ('recommendation_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='wikidata.Recommendation')),
                ('linked_property', models.ForeignKey(to='annotationsets.LinkedProperty')),
                ('property', models.ForeignKey(blank=True, to='annotationsets.Property', null=True)),
            ],
            bases=('wikidata.recommendation',),
        ),
        migrations.AddField(
            model_name='recommendation',
            name='reasons',
            field=models.ManyToManyField(to='wikidata.ReasonForRecommendation', blank=True),
        ),
        migrations.AddField(
            model_name='recommendation',
            name='user',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
