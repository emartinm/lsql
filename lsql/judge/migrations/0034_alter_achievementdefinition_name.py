# Generated by Django 3.2 on 2021-05-01 17:50

import django.core.serializers.json
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('judge', '0033_alter_problem_language'),
    ]

    operations = [
        migrations.AlterField(
            model_name='achievementdefinition',
            name='name',
            field=models.JSONField(blank=True, default=None, encoder=django.core.serializers.json.DjangoJSONEncoder, null=True),
        ),
    ]