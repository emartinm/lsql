from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings
from django.core.validators import MinLengthValidator
from django.contrib.postgres.fields import JSONField
from django.core.serializers.json import DjangoJSONEncoder

import markdown
from lxml import html
import logging

from .oracleDriver import OracleExecutor


logger = logging.getLogger(__name__)

# Create your models here.


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

    def clean(self):
        """Creates HTML versions from MarkDown"""
        super().clean()
        self.name_html = markdown_to_html(self.name_md, remove_initial_p=True)
        self.description_html = markdown_to_html(self.description_md, remove_initial_p=False)

    def __str__(self):
        return html.fromstring(self.description_html).text_content()


class Problem(models.Model):
    title_md = models.CharField(max_length=100)
    title_html = models.CharField(max_length=200, default='', blank=True)
    text_md = models.CharField(max_length=5000)
    text_html = models.CharField(max_length=10000, default='', blank=True)
    create_sql = models.CharField(max_length=20000)
    insert_sql = models.CharField(max_length=20000)
    initial_db = JSONField(encoder=DjangoJSONEncoder, default=None, blank=True, null=True)
    min_stmt = models.PositiveIntegerField(default=1)
    max_stmt = models.PositiveIntegerField(default=1)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    creation_date = models.DateTimeField(auto_now_add=True)
    position = models.PositiveIntegerField(default=1, null=False)

    def clean(self):
        """Check the number of statements and creates HTML versions from MarkDown"""
        super().clean()

        if self.min_stmt > self.max_stmt:
            raise ValidationError('Invalid statement range', code='invalid_stmt_range')

        self.title_html = markdown_to_html(self.title_md, remove_initial_p=True)
        self.text_html = markdown_to_html(self.text_md, remove_initial_p=False)

    def __str__(self):
        return html.fromstring(self.title_html).text_content()


class SelectProblem(Problem):
    check_order = models.BooleanField(default=False)
    solution = models.CharField(max_length=5000, validators=[MinLengthValidator(1)])
    expected_result = JSONField(encoder=DjangoJSONEncoder, default=None, blank=True, null=True)

    def clean(self):
        """Executes the problem and stores the expected result"""
        super().clean()
        executor = OracleExecutor.get()
        res = executor.execute_select_test(self.create_sql, self.insert_sql, self.solution, output_db=True)
        self.expected_result = res['result']
        self.initial_db = res['db']
        logger.error(f'***** {res}')


class DMLProblem(Problem):
    check_order = models.BooleanField(default=False)
    solution = models.CharField(max_length=5000, validators=[MinLengthValidator(1)])
    expected_result = JSONField(encoder=DjangoJSONEncoder)


class FunctionProblem(Problem):
    check_order = models.BooleanField(default=False)
    solution = models.CharField(max_length=5000, validators=[MinLengthValidator(1)])
    expected_result = JSONField(encoder=DjangoJSONEncoder)


class ProcProblem(Problem):
    check_order = models.BooleanField(default=False)
    solution = models.CharField(max_length=5000, validators=[MinLengthValidator(1)])
    proc_call = models.CharField(max_length=1000, validators=[MinLengthValidator(1)])
    expected_result = JSONField(encoder=DjangoJSONEncoder)


class TriggerProblem(Problem):
    check_order = models.BooleanField(default=False)
    solution = models.CharField(max_length=5000, validators=[MinLengthValidator(1)])
    tests = models.CharField(max_length=1000, validators=[MinLengthValidator(1)])
    expected_result = JSONField(encoder=DjangoJSONEncoder)


class Submission(models.Model):
    creation_date = models.DateTimeField(auto_now_add=True)
    code = models.CharField(max_length=5000, validators=[MinLengthValidator(1)])
    veredict_code = models.PositiveSmallIntegerField()
    veredict_message = models.CharField(max_length=5000, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
