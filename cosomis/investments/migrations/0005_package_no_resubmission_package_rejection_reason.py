# Generated by Django 4.1.1 on 2024-02-16 09:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("investments", "0004_delete_organization"),
    ]

    operations = [
        migrations.AddField(
            model_name="package",
            name="no_resubmission",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="package",
            name="rejection_reason",
            field=models.TextField(blank=True, null=True),
        ),
    ]
