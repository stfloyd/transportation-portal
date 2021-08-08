# Generated by Django 3.0.6 on 2020-05-26 12:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transportation', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='triprequest',
            name='vehicle_type',
            field=models.PositiveSmallIntegerField(choices=[(0, 'Unknown'), (1, 'Car'), (2, 'Passenger Van'), (3, 'Cargo Van'), (4, 'Bus'), (5, 'Coach Bus'), (6, 'Road Bus'), (7, 'Truck'), (8, 'Non-CDL Bus'), (9, 'Golf Cart')], default=0, verbose_name='Vehicle Type'),
        ),
    ]
