from django.db import models


class Organization(models.Model):
    id = models.AutoField(primary_key=True)

    name = models.CharField(max_length=50)

    def __str__(self): return self.name


class Department(models.Model):
    num = models.CharField(
        primary_key=True,
        max_length=20,
        verbose_name='Department #'
    )

    org = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='departments',
        verbose_name='Organization'
    )

    name = models.CharField(
        max_length=50,
        verbose_name='Name'
    )

    def __str__(self): return self.name


class Budget(models.Model):
    num = models.CharField(
        primary_key=True,
        max_length=20,
        verbose_name='Budget #'
    )

    org = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        verbose_name='Organization',
        related_name='budgets'
    )

    name = models.CharField(
        max_length=50,
        verbose_name='Name'
    )

    def __str__(self): return self.name
