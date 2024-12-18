# Generated by Django 4.1.1 on 2024-12-18 13:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administrativelevels', '0025_administrativelevel_geo_segment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='administrativelevel',
            name='type',
            field=models.CharField(choices=[('village', 'Village'), ('arrondissement', 'Arrondissement'), ('commune', 'Commune'), ('département', 'Department'), ('country', 'Country')], default='village', max_length=255, verbose_name='Type'),
        ),
    ]
