# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('annotationsets', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='linkedconcept',
            name='super_types',
            field=models.ManyToManyField(related_name='super_types_rel_+', to='annotationsets.LinkedConcept', blank=True),
        ),
    ]
