# Generated by Django 4.1.1 on 2024-10-28 15:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administrativelevels', '0020_administrativelevel_code_loc'),
    ]

    operations = [
        migrations.CreateModel(
            name='GeoSegment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_date', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_date', models.DateTimeField(auto_now=True, null=True)),
                ('latitude_northwest', models.DecimalField(blank=True, db_index=True, decimal_places=6, max_digits=9, null=True, verbose_name='Latitude')),
                ('longitude_northwest', models.DecimalField(blank=True, db_index=True, decimal_places=6, max_digits=9, null=True, verbose_name='Longitude')),
                ('latitude_northeast', models.DecimalField(blank=True, db_index=True, decimal_places=6, max_digits=9, null=True, verbose_name='Latitude')),
                ('longitude_northeast', models.DecimalField(blank=True, db_index=True, decimal_places=6, max_digits=9, null=True, verbose_name='Longitude')),
                ('latitude_southeast', models.DecimalField(blank=True, db_index=True, decimal_places=6, max_digits=9, null=True, verbose_name='Latitude')),
                ('longitude_southeast', models.DecimalField(blank=True, db_index=True, decimal_places=6, max_digits=9, null=True, verbose_name='Longitude')),
                ('latitude_southwest', models.DecimalField(blank=True, db_index=True, decimal_places=6, max_digits=9, null=True, verbose_name='Latitude')),
                ('longitude_southwest', models.DecimalField(blank=True, db_index=True, decimal_places=6, max_digits=9, null=True, verbose_name='Longitude')),
                ('cluster_id', models.CharField(blank=True, max_length=255, null=True, verbose_name='Cluster ID')),
                ('country', models.CharField(blank=True, max_length=255, null=True, verbose_name='Country code')),
                ('lc_gencat_20', models.CharField(blank=True, max_length=255, null=True, verbose_name='LC gencat 20')),
                ('region', models.CharField(blank=True, max_length=255, null=True, verbose_name='Region')),
                ('acled_bexrem_sum', models.FloatField(blank=True, null=True)),
                ('acled_civvio_sum', models.FloatField(blank=True, null=True)),
                ('acled_riodem_sum', models.FloatField(blank=True, null=True)),
                ('fatal_sum', models.FloatField(blank=True, null=True)),
                ('grid_id', models.IntegerField(blank=True, null=True, verbose_name='Grid ID')),
                ('popplace_travel', models.FloatField(blank=True, null=True)),
                ('population_20', models.FloatField(blank=True, null=True)),
                ('population_2000_diff', models.FloatField(blank=True, null=True)),
                ('pr_avg_2020_diff', models.FloatField(blank=True, null=True)),
                ('road_len', models.FloatField(blank=True, null=True)),
                ('tmmx_avg_2020_diff', models.FloatField(blank=True, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
