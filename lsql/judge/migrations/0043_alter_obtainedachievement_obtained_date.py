# Generated by Django 3.2.8 on 2021-12-08 12:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('judge', '0042_auto_20210907_1629'),
    ]

    operations = [
        migrations.AlterField(
            model_name='obtainedachievement',
            name='obtained_date',
            field=models.DateTimeField(),
        ),
    ]
