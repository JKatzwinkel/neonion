# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='url',
            field=models.URLField(max_length=500, null=True, verbose_name=b'url'),
        ),
        migrations.AlterField(
            model_name='document',
            name='concept_set',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='annotationsets.ConceptSet', null=True),
        ),
    ]
