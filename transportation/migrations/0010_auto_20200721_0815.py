# Generated by Django 3.0.7 on 2020-07-21 13:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('transportation', '0009_auto_20200709_1101'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='triprequest',
            options={'get_latest_by': 'updated', 'ordering': ['updated']},
        ),
    ]
