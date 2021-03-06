# Generated by Django 3.0.7 on 2020-06-25 22:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transportation', '0004_triprequest_requested_driver'),
    ]

    operations = [
        migrations.AlterField(
            model_name='driver',
            name='birth_date',
            field=models.DateField(blank=True, null=True, verbose_name='Date of Birth'),
        ),
        migrations.AlterField(
            model_name='driver',
            name='expiration_date',
            field=models.DateField(blank=True, null=True, verbose_name='License Expiration Date'),
        ),
        migrations.AlterField(
            model_name='driver',
            name='license_num',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name='License #'),
        ),
        migrations.AlterField(
            model_name='driver',
            name='state',
            field=models.CharField(blank=True, max_length=2, null=True, verbose_name='State'),
        ),
    ]
