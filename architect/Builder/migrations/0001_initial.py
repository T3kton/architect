# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import architect.fields


class Migration(migrations.Migration):

    dependencies = [
        ('Contractor', '0001_initial'),
        ('Plan', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Action',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('action', models.CharField(max_length=10, choices=[('build', 'build'), ('destroy', 'destroy'), ('rebuild', 'rebuild'), ('move', 'move')])),
                ('state', architect.fields.JSONField(default={}, blank=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Instance',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('state', models.CharField(max_length=10, choices=[('new', 'new'), ('built', 'built'), ('destroyed', 'destroyed'), ('processing', 'processing')])),
                ('hostname', models.CharField(max_length=200, unique=True)),
                ('foundation_id', models.IntegerField(unique=True, null=True, blank=True)),
                ('structure_id', models.IntegerField(unique=True, null=True, blank=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Job',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('target', models.CharField(max_length=10, choices=[('foundation', 'foundation'), ('structure', 'structure')])),
                ('task', models.CharField(max_length=7, choices=[('build', 'build'), ('destroy', 'destroy'), ('move', 'move')])),
                ('state', models.CharField(max_length=7, choices=[('new', 'new'), ('waiting', 'waiting'), ('done', 'done'), ('error', 'error')])),
                ('web_hook_token', models.CharField(max_length=40, null=True, blank=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('action', models.OneToOneField(to='Builder.Action', on_delete=django.db.models.deletion.PROTECT)),
            ],
        ),
        migrations.CreateModel(
            name='ComplexInstance',
            fields=[
                ('instance_ptr', models.OneToOneField(auto_created=True, to='Builder.Instance', serialize=False, primary_key=True, parent_link=True)),
                ('nonce', models.CharField(max_length=26, unique=True)),
                ('complex', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='Contractor.Complex')),
            ],
            bases=('Builder.instance',),
        ),
        migrations.CreateModel(
            name='TypedInstance',
            fields=[
                ('instance_ptr', models.OneToOneField(auto_created=True, to='Builder.Instance', serialize=False, primary_key=True, parent_link=True)),
                ('site_id', models.CharField(max_length=40)),
                ('foundation_type', models.CharField(max_length=50)),
                ('address_block_id', models.IntegerField()),
                ('address_offset', models.IntegerField()),
            ],
            bases=('Builder.instance',),
        ),
        migrations.AddField(
            model_name='instance',
            name='blueprint',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='Contractor.BluePrint'),
        ),
        migrations.AddField(
            model_name='instance',
            name='plan',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='Plan.Plan'),
        ),
        migrations.AddField(
            model_name='action',
            name='instance',
            field=models.OneToOneField(to='Builder.Instance', on_delete=django.db.models.deletion.PROTECT),
        ),
    ]
