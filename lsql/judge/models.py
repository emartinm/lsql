# -*- coding: utf-8 -*-
"""
Copyright Enrique Martín <emartinm@ucm.es> 2020

Models to store objects in the DB
"""

from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings
from django.core.validators import MinLengthValidator
from django.contrib.postgres.fields import JSONField
from django.core.serializers.json import DjangoJSONEncoder


import markdown
from lxml import html
from logzero import logger

from .feedback import compare_select_results, compare_db_results, compare_function_results
from .oracleDriver import OracleExecutor
from .types import VeredictCode, ProblemType
from .parse import load_select_problem, load_dml_problem, load_function_problem, load_proc_problem, \
    load_trigger_problem, parse_many_problems


def markdown_to_html(md, remove_initial_p=False):
    """Converts a markdown string into HTML (posibbly removing initial paragraph <p>....</p>"""
    html_code = markdown.markdown(md, output_format='html5').strip()
    tree = html.fromstring(html_code)
    if remove_initial_p and tree.tag == 'p':
        # Removes the surrounding <p></p> in one paragraph html
        html_code = html_code[3:-4]
    return html_code


class Collection(models.Model):
    name_md = models.CharField(max_length=100, validators=[MinLengthValidator(1)])
    name_html = models.CharField(max_length=200, default='', blank=True)
    position = models.PositiveIntegerField(default=1, null=False)
    description_md = models.CharField(max_length=5000, validators=[MinLengthValidator(1)])
    description_html = models.CharField(max_length=10000, default='', blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    creation_date = models.DateTimeField(auto_now_add=True)
    # (Dirty) trick to load problems from a ZIP fil by editing a collection using the standard admin interface of Django
    zipfile = models.FileField(upload_to='problem_zips/', default=None, blank=True, null=True)

    def clean(self):
        # Loads data from file and generates HTML from Markdown
        if self.zipfile:
            problems = parse_many_problems(self.zipfile, self)
            for p in problems:
                p.clean()
                p.save()
                logger.debug(f'Added problem {type(p)} "{p}" from ZIP (batch)')
            self.zipfile = None  # Avoids storing the file in the filysystem

        super().clean()
        self.name_html = markdown_to_html(self.name_md, remove_initial_p=True)
        self.description_html = markdown_to_html(self.description_md, remove_initial_p=False)

    def __str__(self):
        # String to show in the Admin
        return html.fromstring(self.name_html).text_content()

    def problems(self):
        # Returns a list of Problem objects in the collection using the inverse FK from Problem to Collection
        return self.problem_set.filter()

    def num_problems(self):
        # Number of problems in the collection
        return self.problems().count()

    def num_solved_by_user(self, user):
        return Submission.objects.filter(veredict_code='AC', problem__collection=self, user=user)\
            .distinct('problem').count()


class Problem(models.Model):
    title_md = models.CharField(max_length=100, blank=True)
    title_html = models.CharField(max_length=200)
    text_md = models.TextField(max_length=5000, blank=True)
    text_html = models.TextField(max_length=10000)
    create_sql = models.TextField(max_length=20000, blank=True)
    insert_sql = models.TextField(max_length=20000, blank=True)
    initial_db = JSONField(encoder=DjangoJSONEncoder, default=None, blank=True, null=True)
    min_stmt = models.PositiveIntegerField(default=1)
    max_stmt = models.PositiveIntegerField(default=1)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    creation_date = models.DateTimeField(auto_now_add=True)
    position = models.PositiveIntegerField(default=1, null=False)
    # (Dirty) trick to upload ZIP files using the standard admin interface of Django
    zipfile = models.FileField(upload_to='problem_zips/', default=None, blank=True, null=True)

    def clean(self):
        """Check the number of statements and creates HTML versions from MarkDown"""
        super().clean()

        if self.min_stmt > self.max_stmt:
            raise ValidationError('Invalid statement range', code='invalid_stmt_range')

        self.title_html = markdown_to_html(self.title_md, remove_initial_p=True)
        self.text_html = markdown_to_html(self.text_md, remove_initial_p=False)

    def __str__(self):
        return html.fromstring(self.title_html).text_content()

    def template(self):
        raise NotImplementedError

    def judge(self, code, executor):
        raise NotImplementedError

    def problem_type(self):
        raise NotImplementedError

    def solved_by_user(self, user):
        return Submission.objects.filter(user=user, problem=self, veredict_code=VeredictCode.AC).count() > 0

    def num_submissions_by_user(self, user):
        return Submission.objects.filter(problem=self, user=user).count()


class SelectProblem(Problem):
    check_order = models.BooleanField(default=False)
    solution = models.TextField(max_length=5000, validators=[MinLengthValidator(1)], blank=True)
    expected_result = JSONField(encoder=DjangoJSONEncoder, default=None, blank=True, null=True)

    def clean(self):
        """Executes the problem and stores the expected result"""
        try:
            if self.zipfile:
                # Replaces the fields with the information from the file
                load_select_problem(self, self.zipfile)

            super().clean()
            executor = OracleExecutor.get()
            res = executor.execute_select_test(self.create_sql, self.insert_sql, self.solution, output_db=True)
            self.expected_result = res['result']
            self.initial_db = res['db']
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(e)

    def template(self):
        return 'problem_select.html'

    def judge(self, code, executor):
        oracle_result = executor.execute_select_test(self.create_sql, self.insert_sql, code, output_db=False)
        return compare_select_results(self.expected_result, oracle_result['result'], self.check_order)

    def problem_type(self):
        return ProblemType.SELECT


class DMLProblem(Problem):
    check_order = models.BooleanField(default=False)
    solution = models.TextField(max_length=5000, validators=[MinLengthValidator(1)], blank=True)
    expected_result = JSONField(encoder=DjangoJSONEncoder, blank=True)

    def clean(self):
        """Executes the problem and stores the expected result"""
        try:
            if self.zipfile:
                # Replaces the fields with the information from the file
                load_dml_problem(self, self.zipfile)

            super().clean()
            executor = OracleExecutor.get()
            res = executor.execute_dml_test(self.create_sql, self.insert_sql, self.solution, pre_db=True)
            self.expected_result = res['post']
            self.initial_db = res['pre']
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(e)

    def template(self):
        return 'problem_dml.html'

    def judge(self, code, executor):
        oracle_result = executor.execute_dml_test(self.create_sql, self.insert_sql, code, pre_db=False)
        return compare_db_results(self.expected_result, oracle_result['post'])

    def problem_type(self):
        return ProblemType.DML


class FunctionProblem(Problem):
    check_order = models.BooleanField(default=False)
    solution = models.TextField(max_length=5000, validators=[MinLengthValidator(1)], blank=True)
    calls = models.TextField(max_length=5000, validators=[MinLengthValidator(1)], default='', blank=True)
    expected_result = JSONField(encoder=DjangoJSONEncoder, blank=True)

    def clean(self):
        """Executes the problem and stores the expected result"""
        try:
            if self.zipfile:
                # Replaces the fields with the information from the file
                load_function_problem(self, self.zipfile)

            super().clean()
            executor = OracleExecutor.get()
            res = executor.execute_function_test(self.create_sql, self.insert_sql, self.solution, self.calls)
            self.expected_result = res['results']
            self.initial_db = res['db']
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(e)

    def template(self):
        return 'problem_function.html'

    def expected_result_as_table(self):
        rows = [[call, result] for call, result in self.expected_result.items()]
        return {'rows': rows, 'header': [('Llamada', None), ('Resultado', None)]}

    def judge(self, code, executor):
        oracle_result = executor.execute_function_test(self.create_sql, self.insert_sql, code, self.calls)
        return compare_function_results(self.expected_result, oracle_result['results'])

    def problem_type(self):
        return ProblemType.FUNCTION


class ProcProblem(Problem):
    check_order = models.BooleanField(default=False)
    solution = models.TextField(max_length=5000, validators=[MinLengthValidator(1)], blank=True)
    proc_call = models.TextField(max_length=1000, validators=[MinLengthValidator(1)], blank=True)
    expected_result = JSONField(encoder=DjangoJSONEncoder, blank=True)

    def template(self):
        return 'problem_proc.html'

    def clean(self):
        """Executes the problem and stores the expected result"""
        try:
            if self.zipfile:
                # Replaces the fields with the information from the file
                load_proc_problem(self, self.zipfile)
                self.zipfile = None  # Avoid saving the file to the filesystem

            super().clean()
            executor = OracleExecutor.get()
            res = executor.execute_proc_test(self.create_sql, self.insert_sql, self.solution, self.proc_call,
                                             pre_db=True)
            self.expected_result = res['post']
            self.initial_db = res['pre']
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(e)

    def judge(self, code, executor):
        oracle_result = executor.execute_proc_test(self.create_sql, self.insert_sql, code, self.proc_call, pre_db=False)
        return compare_db_results(self.expected_result, oracle_result['post'])

    def problem_type(self):
        return ProblemType.PROC


class TriggerProblem(Problem):
    check_order = models.BooleanField(default=False)
    solution = models.TextField(max_length=5000, validators=[MinLengthValidator(1)], blank=True)
    tests = models.TextField(max_length=1000, validators=[MinLengthValidator(1)], blank=True)
    expected_result = JSONField(encoder=DjangoJSONEncoder, blank=True)

    def template(self):
        return 'problem_trigger.html'  # The same template works

    def clean(self):
        """Executes the problem and stores the expected result"""
        try:
            if self.zipfile:
                # Replaces the fields with the information from the file
                load_trigger_problem(self, self.zipfile)

            super().clean()
            executor = OracleExecutor.get()
            res = executor.execute_trigger_test(self.create_sql, self.insert_sql, self.solution, self.tests, pre_db=True)
            self.expected_result = res['post']
            self.initial_db = res['pre']
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(e)

    def judge(self, code, executor):
        oracle_result = executor.execute_trigger_test(self.create_sql, self.insert_sql, code, self.tests, pre_db=False)
        return compare_db_results(self.expected_result, oracle_result['post'])

    def problem_type(self):
        return ProblemType.TRIGGER


class Submission(models.Model):
    creation_date = models.DateTimeField(auto_now_add=True)
    code = models.CharField(max_length=5000, validators=[MinLengthValidator(1)])
    veredict_code = models.CharField(
        max_length=3,
        choices=VeredictCode.choices,
        default=VeredictCode.AC
    )
    veredict_message = models.CharField(max_length=5000, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.pk} - {self.user.email} - {self.veredict_code}"
