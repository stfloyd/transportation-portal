# Generated by Django 3.0.6 on 2020-05-26 18:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transportation', '0002_triprequest_vehicle_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='vehicle',
            name='notes',
            field=models.TextField(blank=True),
        ),
    ]