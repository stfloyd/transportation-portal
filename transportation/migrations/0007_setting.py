# Generated by Django 3.0.8 on 2020-07-05 21:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transportation', '0006_auto_20200630_1235'),
    ]

    operations = [
        migrations.CreateModel(
            name='Setting',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('key', models.CharField(max_length=255)),
                ('value', models.TextField()),
            ],
        ),
    ]
