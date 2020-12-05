# Generated by Django 3.0.7 on 2020-06-17 18:10

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('judge', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='collection',
            name='description_html',
            field=models.CharField(blank=True, max_length=10000),
        ),
        migrations.AlterField(
            model_name='collection',
            name='description_md',
            field=models.CharField(max_length=5000, validators=[django.core.validators.MinLengthValidator(1)]),
        ),
        migrations.AlterField(
            model_name='collection',
            name='name_html',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='collection',
            name='name_md',
            field=models.CharField(max_length=100, validators=[django.core.validators.MinLengthValidator(1)]),
        ),
        migrations.AlterField(
            model_name='dmlproblem',
            name='solution',
            field=models.CharField(max_length=5000, validators=[django.core.validators.MinLengthValidator(1)]),
        ),
        migrations.AlterField(
            model_name='functionproblem',
            name='proc_call',
            field=models.CharField(max_length=1000, validators=[django.core.validators.MinLengthValidator(1)]),
        ),
        migrations.AlterField(
            model_name='functionproblem',
            name='solution',
            field=models.CharField(max_length=5000, validators=[django.core.validators.MinLengthValidator(1)]),
        ),
        migrations.AlterField(
            model_name='selectproblem',
            name='solution',
            field=models.CharField(max_length=5000, validators=[django.core.validators.MinLengthValidator(1)]),
        ),
        migrations.AlterField(
            model_name='submission',
            name='code',
            field=models.CharField(max_length=5000, validators=[django.core.validators.MinLengthValidator(1)]),
        ),
        migrations.AlterField(
            model_name='triggerproblem',
            name='solution',
            field=models.CharField(max_length=5000, validators=[django.core.validators.MinLengthValidator(1)]),
        ),
        migrations.AlterField(
            model_name='triggerproblem',
            name='tests',
            field=models.CharField(max_length=1000, validators=[django.core.validators.MinLengthValidator(1)]),
        ),
    ]