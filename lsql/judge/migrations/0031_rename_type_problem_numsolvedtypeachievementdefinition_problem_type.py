# Generated by Django 3.2 on 2021-04-20 15:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('judge', '0030_numsubmissionsproblemsachievementdefinition'),
    ]

    operations = [
        migrations.RenameField(
            model_name='numsolvedtypeachievementdefinition',
            old_name='type_problem',
            new_name='problem_type',
        ),
    ]
