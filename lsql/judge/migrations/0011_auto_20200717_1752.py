# Generated by Django 3.0.7 on 2020-07-17 15:52

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('judge', '0010_auto_20200717_1735'),
    ]

    operations = [
        migrations.AlterField(
            model_name='problem',
            name='create_sql',
            field=models.CharField(blank=True, max_length=20000, null=True),
        ),
        migrations.AlterField(
            model_name='problem',
            name='insert_sql',
            field=models.CharField(blank=True, max_length=20000, null=True),
        ),
        migrations.AlterField(
            model_name='problem',
            name='text_md',
            field=models.CharField(blank=True, max_length=5000),
        ),
        migrations.AlterField(
            model_name='problem',
            name='title_md',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='selectproblem',
            name='solution',
            field=models.CharField(blank=True, max_length=5000, validators=[django.core.validators.MinLengthValidator(1)]),
        ),
    ]