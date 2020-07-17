from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings
from django.core.validators import MinLengthValidator
from django.contrib.postgres.fields import JSONField
from django.core.serializers.json import DjangoJSONEncoder


import markdown
from lxml import html
import logging

from .feedback import compare_select_results, compare_db_results, compare_function_results
from .oracleDriver import OracleExecutor
from .types import VeredictCode, ProblemType
from .parse import load_select_problem, load_dml_problem, load_function_problem, load_proc_problem, load_trigger_problem

logger = logging.getLogger(__name__)


def markdown_to_html(md, remove_initial_p=False):
    html_code = markdown.markdown(md, output_format='html5').strip()
    tree = html.fromstring(html_code)
    if remove_initial_p and tree.tag == 'p':
        # Removes the surrounding <p></p> in one paragraph html
        html_code = html_code[3:-4]
    return html_code


class Collection(models.Model):
    name_md = models.CharField(max_length=100, validators=[MinLengthValidator(1)])
    name_html = models.CharField(max_length=200, default='', blank=True)
    position = models.PositiveIntegerField()
    description_md = models.CharField(max_length=5000, validators=[MinLengthValidator(1)])
    description_html = models.CharField(max_length=10000, default='', blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    creation_date = models.DateTimeField(auto_now_add=True)
    # zipfile = models.FileField(upload_to='collection_zips/', default=None, blank=True, null=True)

    def clean(self):
        """Creates HTML versions from MarkDown"""
        super().clean()
        self.name_html = markdown_to_html(self.name_md, remove_initial_p=True)
        self.description_html = markdown_to_html(self.description_md, remove_initial_p=False)

    def __str__(self):
        return html.fromstring(self.description_html).text_content()

    def problems(self):
        return Problem.objects.filter(collection=self)

    def num_problems(self):
        return self.problems().count()

    def num_solved_by_user(self, user):
        # FIXME
        return 2


class Problem(models.Model):
    title_md = models.CharField(max_length=100, blank=True)
    title_html = models.CharField(max_length=200, default='')
    text_md = models.CharField(max_length=5000, blank=True)
    text_html = models.CharField(max_length=10000, default='')
    create_sql = models.CharField(max_length=20000, null=True, blank=True)
    insert_sql = models.CharField(max_length=20000, null=True, blank=True)
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


class SelectProblem(Problem):
    check_order = models.BooleanField(default=False)
    solution = models.CharField(max_length=5000, validators=[MinLengthValidator(1)], blank=True)
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
    solution = models.CharField(max_length=5000, validators=[MinLengthValidator(1)])
    expected_result = JSONField(encoder=DjangoJSONEncoder)

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
    solution = models.CharField(max_length=5000, validators=[MinLengthValidator(1)])
    calls = models.CharField(max_length=5000, validators=[MinLengthValidator(1)], default='')
    expected_result = JSONField(encoder=DjangoJSONEncoder)

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
    solution = models.CharField(max_length=5000, validators=[MinLengthValidator(1)])
    proc_call = models.CharField(max_length=1000, validators=[MinLengthValidator(1)])
    expected_result = JSONField(encoder=DjangoJSONEncoder)

    def template(self):
        return 'problem_dml.html'  # The same template works

    def clean(self):
        """Executes the problem and stores the expected result"""
        try:
            if self.zipfile:
                # Replaces the fields with the information from the file
                load_proc_problem(self, self.zipfile)

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
    solution = models.CharField(max_length=5000, validators=[MinLengthValidator(1)])
    tests = models.CharField(max_length=1000, validators=[MinLengthValidator(1)])
    expected_result = JSONField(encoder=DjangoJSONEncoder)

    def template(self):
        return 'problem_dml.html'  # The same template works

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
