# -*- coding: utf-8 -*-
"""
Copyright Enrique Martín <emartinm@ucm.es> 2020

Models to store objects in the DB
"""
from zipfile import ZipFile
import markdown
from lxml import html
from logzero import logger
from model_utils.managers import InheritanceManager

import django.utils.timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db.models import JSONField, Subquery
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import translation

from .feedback import compare_select_results, compare_db_results, compare_function_results, compare_discriminant_db
from .oracle_driver import OracleExecutor
from .types import VeredictCode, ProblemType
from .parse import load_select_problem, load_dml_problem, load_function_problem, load_proc_problem, \
    load_trigger_problem, load_discriminant_problem
from .exceptions import ZipFileParsingException


def markdown_to_html(markdown_text, remove_initial_p=False):
    """Converts a markdown string into HTML (posibbly removing initial paragraph <p>....</p>"""
    html_code = markdown.markdown(markdown_text, output_format='html5').strip()
    tree = html.fromstring(html_code)
    if remove_initial_p and tree.tag == 'p':
        # Removes the surrounding <p></p> in one paragraph html
        html_code = html_code[3:-4]
    return html_code


def load_many_problems(file, collection):
    """Given a ZIP file containing several ZIP files (each one a problem),
       insert the problems into collection"""
    problems = list()
    try:
        with ZipFile(file) as zfile:
            for filename in zfile.infolist():
                with zfile.open(filename) as curr_file:
                    problem = load_problem_from_file(curr_file)
                    problem.collection = collection
                    problem.author = collection.author
                    problems.append(problem)
    except ZipFileParsingException as excp:
        raise ZipFileParsingException('{}: {}'.format(filename.filename, excp)) from excp
    except Exception as excp:
        raise ZipFileParsingException("{}: {}".format(type(excp), excp)) from excp
    return problems


def load_problem_from_file(file):
    """Try to load all the types of problem from file, in order"""
    problem_types = [(SelectProblem, load_select_problem),
                     (DMLProblem, load_dml_problem),
                     (FunctionProblem, load_function_problem),
                     (ProcProblem, load_proc_problem),
                     (TriggerProblem, load_trigger_problem),
                     (DiscriminantProblem, load_discriminant_problem)
                     ]

    for pclass, load_fun in problem_types:
        problem = pclass()
        try:
            load_fun(problem, file)
            return problem
        except ZipFileParsingException:
            # It is not the type, try next one
            pass
    raise ZipFileParsingException(f'Unable to load {file}')


class Collection(models.Model):
    """Collection of problems"""
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
        """Loads and overwrite data from the ZIP file (if it is set) and creates HTML from markdown"""
        try:
            if self.zipfile:
                problems = load_many_problems(self.zipfile, self)
                for problem in problems:
                    problem.clean()
                    problem.save()
                    logger.debug('Added problem %s "%s" from ZIP (batch)', type(problem), problem)
                self.zipfile = None  # Avoids storing the file in the filesystem

            super().clean()
            self.name_html = markdown_to_html(self.name_md, remove_initial_p=True)
            self.description_html = markdown_to_html(self.description_md, remove_initial_p=False)
        except Exception as excp:
            raise ValidationError(excp) from excp

    def __str__(self):
        """String to show in the Admin"""
        return html.fromstring(self.name_html).text_content() if self.name_html else self.name_md

    def problems(self):
        """Returns a list of Problem objects in the collection using the inverse FK from Problem to Collection"""
        return self.problem_set.all().order_by('position', '-creation_date')

    def num_problems(self):
        """Number of problems in the collection"""
        return self.problems().count()

    def num_solved_by_user(self, user):
        """Number of problems solved by user in this collection"""
        return Submission.objects.filter(veredict_code='AC', problem__collection=self, user=user) \
            .distinct('problem').count()

    def languages(self):
        """Set with all the languages of the collection"""
        return list(self.problems().order_by('language').distinct('language').values_list('language', flat=True))


class Problem(models.Model):
    """Base class for problems, with common attributes and methods"""
    __INSERT_SEPARATION = "-- @new data base@"
    title_md = models.CharField(max_length=100, blank=True)
    title_html = models.CharField(max_length=200)
    text_md = models.TextField(max_length=5000, blank=True)
    text_html = models.TextField(max_length=10000)
    language = models.CharField(max_length=7, choices=settings.LANGUAGES, default=settings.LANGUAGE_CODE)
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

    # To query Problem to obtain subclass objects with '.select_subclasses()'
    objects = InheritanceManager()

    def clean(self):
        """Check the number of statements and creates HTML versions from MarkDown"""
        super().clean()

        if self.min_stmt > self.max_stmt:
            raise ValidationError('Invalid statement range', code='invalid_stmt_range')

        self.title_html = markdown_to_html(self.title_md, remove_initial_p=True)
        self.text_html = markdown_to_html(self.text_md, remove_initial_p=False)

    def __str__(self):
        """String to show in the Admin interface"""
        return html.fromstring(self.title_html).text_content()

    def template(self):
        """Name of the HTML template used to show the problem"""
        raise NotImplementedError

    def judge(self, code, executor):
        """Assess the code with the user solution using a DB executor"""
        raise NotImplementedError

    def problem_type(self):
        """Return an enumeration ProblemType with the problem type"""
        raise NotImplementedError

    def solved_by_user(self, user) -> bool:
        """Whether user has solved the problem or not"""
        return Submission.objects.filter(user=user, problem=self, veredict_code=VeredictCode.AC).count() > 0

    def num_submissions_by_user(self, user):
        """Number of user submissions to the problem"""
        return Submission.objects.filter(problem=self, user=user).count()

    def solved_n_position(self, position):
        """User (non-staff and active) who solved the problem in 'position' position"""
        active_students = get_user_model().objects.filter(is_staff=False, is_active=True)
        pks = Submission.objects.filter(problem=self, veredict_code=VeredictCode.AC, user__in=active_students) \
            .order_by('user', 'pk').distinct('user').values_list('pk', flat=True)
        subs = Submission.objects.filter(pk__in=pks).order_by('pk')[position - 1:position]
        if len(subs) > 0 and subs[0] is not None:
            return subs[0].user
        return None

    def solved_first(self):
        """User (non-staff and active) who solved first"""
        return self.solved_n_position(1)

    def solved_second(self):
        """User (non-staff and active) who solved second"""
        return self.solved_n_position(2)

    def solved_third(self):
        """User (non-staff and active) who solved third"""
        return self.solved_n_position(3)

    def solved_position(self, user):
        """Position that user solved the problem (ignoring staff and inactive users). If not solved return None"""
        if self.solved_by_user(user):
            active_students = get_user_model().objects.filter(is_staff=False, is_active=True)
            iterator = 1
            users_ac = (Submission.objects.
                        filter(problem=self, user__in=active_students, veredict_code=VeredictCode.AC).
                        order_by('pk', 'user').
                        distinct('pk', 'user').
                        values_list('user', flat=True))
            for users in users_ac:
                if users == user.pk:
                    return iterator
                iterator = iterator + 1
        return None

    def insert_sql_list(self):
        """List containing all sql inserts"""
        return self.insert_sql.split(self.__INSERT_SEPARATION)


class SelectProblem(Problem):
    """Problem that requires a SELECT statement as solution"""
    check_order = models.BooleanField(default=False)
    solution = models.TextField(max_length=5000, validators=[MinLengthValidator(1)], blank=True)
    expected_result = JSONField(encoder=DjangoJSONEncoder, default=None, blank=True, null=True)

    def clean(self):
        """ Executes the problem and stores the expected result """
        try:
            if self.zipfile:
                # Replaces the fields with the information from the file
                load_select_problem(self, self.zipfile)
            super().clean()
            executor = OracleExecutor.get()
            self.expected_result = []
            self.initial_db = []
            for insert_sql in self.insert_sql_list():
                res = executor.execute_select_test(self.create_sql, insert_sql,
                                                   self.solution, output_db=True)
                self.expected_result.append(res['result'])
                self.initial_db.append(res['db'])
        except Exception as excp:
            raise ValidationError(excp) from excp

    def template(self):
        return 'problem_select.html'

    def judge(self, code, executor):
        first_insert_sql = self.insert_sql_list()[0]
        oracle_result = executor.execute_select_test(self.create_sql, first_insert_sql, code, output_db=False)
        # Check first code with first db
        veredict, feedback = compare_select_results(self.expected_result[0], oracle_result['result'], self.check_order)
        if veredict != VeredictCode.AC:
            return veredict, feedback
        # Get results using secondary dbs
        insert_sql_extra_list = self.insert_sql_list()[1:]
        initial_db_count = 1
        for insert_sql_extra in insert_sql_extra_list:
            oracle_result_extra = executor.execute_select_test(self.create_sql, insert_sql_extra, code, output_db=False)
            # Check secondary results
            veredict_extra, feedback_extra = compare_select_results(self.expected_result[initial_db_count],
                                                                    oracle_result_extra['result'],
                                                                    self.check_order,
                                                                    self.initial_db[initial_db_count])
            if veredict_extra != VeredictCode.AC:
                return veredict_extra, feedback_extra
            initial_db_count += 1
        # If all results are correct then return first one
        return veredict, feedback

    def problem_type(self):
        return ProblemType.SELECT


class DMLProblem(Problem):
    """Problem that requires one or more DML statements (INSERT, UPDATE, CREATE...) as solution"""
    # IMPORTANT: This problem does not support multiple initial db. It only uses the first db
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
            self.expected_result = [res['post']]
            self.initial_db = [res['pre']]
        except Exception as excp:
            raise ValidationError(excp) from excp

    def template(self):
        return 'problem_dml.html'

    def judge(self, code, executor):
        oracle_result = executor.execute_dml_test(self.create_sql, self.insert_sql, code, pre_db=False,
                                                  min_stmt=self.min_stmt, max_stmt=self.max_stmt)
        return compare_db_results(self.expected_result[0], oracle_result['post'])

    def problem_type(self):
        return ProblemType.DML


class FunctionProblem(Problem):
    """Problem that requires a function definition as solution"""
    # IMPORTANT: This problem does not support multiple initial db. It only uses the first db
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
            self.expected_result = [res['results']]
            self.initial_db = [res['db']]
        except Exception as excp:
            raise ValidationError(excp) from excp

    def template(self):
        return 'problem_function.html'

    def result_as_table(self):
        """Transforms the dict with the expected result in a dict representing a table that can be shown
        in the templates (i.e., we add a suitable header and create rows)"""
        rows = [[call, result] for call, result in self.expected_result[0].items()]
        return {'rows': rows, 'header': [('Llamada', None), ('Resultado', None)]}

    def judge(self, code, executor):
        oracle_result = executor.execute_function_test(self.create_sql, self.insert_sql, code, self.calls)
        return compare_function_results(self.expected_result[0], oracle_result['results'])

    def problem_type(self):
        return ProblemType.FUNCTION


class ProcProblem(Problem):
    """Problem that requires a procedure definition as solution"""
    # IMPORTANT: This problem does not support multiple initial db. It only uses the first db
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
            self.expected_result = [res['post']]
            self.initial_db = [res['pre']]
        except Exception as excp:
            raise ValidationError(excp) from excp

    def judge(self, code, executor):
        oracle_result = executor.execute_proc_test(self.create_sql, self.insert_sql, code, self.proc_call, pre_db=False)
        return compare_db_results(self.expected_result[0], oracle_result['post'])

    def problem_type(self):
        return ProblemType.PROC


class TriggerProblem(Problem):
    """Problem that requires a trigger definition as solution"""
    # IMPORTANT: This problem does not support multiple initial db. It only uses the first db
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
            res = executor.execute_trigger_test(self.create_sql, self.insert_sql,
                                                self.solution, self.tests, pre_db=True)
            self.expected_result = [res['post']]
            self.initial_db = [res['pre']]
        except Exception as excp:
            raise ValidationError(excp) from excp

    def judge(self, code, executor):
        oracle_result = executor.execute_trigger_test(self.create_sql, self.insert_sql, code, self.tests,
                                                      pre_db=False)
        return compare_db_results(self.expected_result[0], oracle_result['post'])

    def problem_type(self):
        return ProblemType.TRIGGER


class DiscriminantProblem(Problem):
    """Problem that requires an INSERT as solution for debug an incorrect query"""
    check_order = models.BooleanField(default=False)
    correct_query = models.TextField(max_length=5000, validators=[MinLengthValidator(1)], blank=True)
    incorrect_query = models.TextField(max_length=5000, validators=[MinLengthValidator(1)], blank=True)
    expected_result = JSONField(encoder=DjangoJSONEncoder, default=None, blank=True, null=True)

    def template(self):
        return 'problem_disc.html'

    def clean(self):
        """Executes the problem and stores the expected result"""
        try:
            if self.zipfile:
                # Replaces the fields with the information from the file
                load_discriminant_problem(self, self.zipfile)
            super().clean()
            executor = OracleExecutor.get()
            self.expected_result = []
            self.initial_db = []
            # In this case (this type of problem) there are only one database
            for insert_sql in self.insert_sql_list():
                res = executor.execute_select_test(self.create_sql, insert_sql,
                                                   self.incorrect_query, output_db=True)
                self.expected_result.append(res['result'])
                self.initial_db.append(res['db'])
        except Exception as excp:
            raise ValidationError(excp) from excp

    def judge(self, code, executor):
        insert_sql = self.insert_sql_list()[0]  # In this type of problem there is only one database
        result = executor.execute_discriminant_test(self.create_sql, insert_sql, code, self.correct_query,
                                                    self.incorrect_query)
        incorrect_result = result["result_incorrect"]
        correct_result = result["result_correct"]
        return compare_discriminant_db(incorrect_result, correct_result, self.check_order)

    def problem_type(self):
        return ProblemType.DISC


class Submission(models.Model):
    """ A user submission """
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


def default_json_lang():
    """ Default values for name and description attributes in AchievementDefinition """
    return {settings.LANGUAGE_CODE: ""}


class AchievementDefinition(models.Model):
    """Abstract class for Achievements"""
    name = JSONField(encoder=DjangoJSONEncoder,
                     default=default_json_lang,
                     blank=True, null=True)
    description = JSONField(encoder=DjangoJSONEncoder,
                            default=default_json_lang,
                            blank=True, null=True)

    # To query Problem to obtain subclass objects with '.select_subclasses()'
    objects = InheritanceManager()

    def check_and_save(self, user):
        """Raise a NotImplementedError, declared function for its children"""
        raise NotImplementedError

    def check_user(self, usr):
        """Check if an user have the achievement"""
        achievements_of_user = ObtainedAchievement.objects.filter(user=usr, achievement_definition=self).count()
        return achievements_of_user > 0

    def refresh(self):
        """Delete the achievement and check if any user have it"""
        ObtainedAchievement.objects.filter(achievement_definition=self).delete()
        all_users = get_user_model().objects.all()
        for usr in all_users:
            self.check_and_save(usr)

    def __str__(self):
        """String for show the achievement name"""
        return self.get_name()

    def get_name(self):
        """Returns the name in the current language"""
        if translation.get_language() in self.name:
            return f"{self.name[translation.get_language()]}"
        return f"{self.name[settings.LANGUAGE_CODE]}"

    def get_description(self):
        """Returns the description in the current language"""
        if translation.get_language() in self.description:
            return f"{self.description[translation.get_language()]}"
        return f"{self.description[settings.LANGUAGE_CODE]}"


class ObtainedAchievement(models.Model):
    """Store info about an obtained achievement"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    obtained_date = models.DateTimeField(default=django.utils.timezone.now)
    achievement_definition = models.ForeignKey(AchievementDefinition, on_delete=models.CASCADE)


class NumSolvedAchievementDefinition(AchievementDefinition, models.Model):
    """Achievement by solving a number of problems"""
    num_problems = models.PositiveIntegerField(default=1, null=False)

    def check_and_save(self, user):
        """Return if an user is deserving for get an achievement, if it is, save that"""
        if not self.check_user(user):
            corrects = Submission.objects.filter(veredict_code=VeredictCode.AC, user=user).distinct("problem").count()
            if corrects >= self.num_problems:
                # First submission of each Problem that user have VeredictCode.AC. Ordered by 'creation_date'
                # Subquery return a list of creation_date of the problems that user have VeredictCode.AC
                order_problem_creation_date = Submission.objects.filter(creation_date__in=Subquery(
                    Submission.objects.filter(veredict_code=VeredictCode.AC, user=user).
                    order_by('problem', 'creation_date').distinct('problem').values('creation_date'))).\
                    order_by('creation_date').values_list('creation_date', flat=True)
                new_achievement = ObtainedAchievement(user=user,
                                                      obtained_date=order_problem_creation_date[self.num_problems-1],
                                                      achievement_definition=self)
                new_achievement.save()
                return True
        return False


class PodiumAchievementDefinition(AchievementDefinition, models.Model):
    """Achievement by solving X problems among the first N"""
    num_problems = models.PositiveIntegerField(default=1, null=False)
    position = models.PositiveIntegerField(default=3, null=False)

    def check_and_save(self, user):
        """Return if an user is deserving for get an achievement, if it is, save that"""
        if not self.check_user(user):
            # First submission of each Problem that user have VeredictCode.AC. Ordered by 'creation_date'
            # Subquery return a list of creation_date of the problems that user have VeredictCode.AC
            order_problem_creation_date = Submission.objects.filter(creation_date__in=Subquery(
                Submission.objects.filter(veredict_code=VeredictCode.AC, user=user).
                order_by('problem', 'creation_date').distinct('problem').values('creation_date'))). \
                order_by('creation_date')
            total = 0
            if order_problem_creation_date.count() >= self.num_problems:
                for sub in order_problem_creation_date:
                    prob = Problem.objects.get(pk=sub.problem.pk)
                    user_pos = prob.solved_position(user)
                    if user_pos is not None and user_pos <= self.position:
                        total = total + 1
                        if total >= self.num_problems:
                            new_achievement = ObtainedAchievement(user=user, obtained_date=sub.creation_date,
                                                                  achievement_definition=self)
                            new_achievement.save()
                            return True
        return False


class NumSolvedCollectionAchievementDefinition(AchievementDefinition, models.Model):
    """Achievement by solving X problems of a Collection"""
    num_problems = models.PositiveIntegerField(default=1, null=False)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)

    def check_and_save(self, user):
        """Return if an user is deserving for get an achievement, if it is, save that"""
        if not self.check_user(user):
            corrects = Submission.objects.filter(veredict_code=VeredictCode.AC, user=user,
                                                 problem__collection=self.collection).distinct("problem").count()
            if corrects >= self.num_problems:
                # First submission of each Problem that user have VeredictCode.AC. Ordered by 'creation_date'
                # Subquery return a list of creation_date of the problems that user have VeredictCode.AC
                order_problem_creation_date = Submission.objects.filter(creation_date__in=Subquery(
                    Submission.objects.filter(veredict_code=VeredictCode.AC, user=user,
                                              problem__collection=self.collection).
                    order_by('problem', 'creation_date').distinct('problem').values('creation_date')
                )).order_by('creation_date').values_list('creation_date', flat=True)
                new_achievement = ObtainedAchievement(user=user,
                                                      obtained_date=order_problem_creation_date[self.num_problems - 1],
                                                      achievement_definition=self)
                new_achievement.save()
                return True
        return False


class NumSolvedTypeAchievementDefinition(AchievementDefinition, models.Model):
    """Achievement by solving X problems of a Type"""
    num_problems = models.PositiveIntegerField(default=1, null=False)
    problem_type = models.CharField(
        max_length=5000,
        choices=list(ProblemType.__members__.items()),
        validators=[MinLengthValidator(1)],
        blank=True
    )

    def check_and_save(self, user):
        """Return if an user is deserving for get an achievement, if it is, save that"""
        if not self.check_user(user):
            count = 0
            # First submission of each Problem that user have VeredictCode.AC. Ordered by 'creation_date'
            # Subquery return a list of creation_date of the problems that user have VeredictCode.AC
            order_problem_creation_date = Submission.objects.filter(creation_date__in=Subquery(
                Submission.objects.filter(veredict_code=VeredictCode.AC, user=user).
                order_by('problem', 'creation_date').distinct('problem').values('creation_date')
            )).order_by('creation_date')
            for sub in order_problem_creation_date:
                problem = Problem.objects.filter(pk=sub.problem.pk).select_subclasses()
                if problem[0].problem_type().name == self.problem_type:
                    count += 1
                    if count >= self.num_problems:
                        new_achievement = ObtainedAchievement(user=user,
                                                              obtained_date=sub.creation_date,
                                                              achievement_definition=self)
                        new_achievement.save()
                        return True
        return False


class NumSubmissionsProblemsAchievementDefinition(AchievementDefinition, models.Model):
    """Achievement by submitting X submissions of Y problems"""
    num_submissions = models.PositiveIntegerField(default=1, null=False)
    num_problems = models.PositiveIntegerField(default=1, null=False)

    def check_and_save(self, user):
        """Return if an user is deserving for get an achievement, if it is, save that"""
        if not self.check_user(user):
            total_submissions = Submission.objects.filter(user=user).count()
            if total_submissions >= self.num_submissions:
                total_prob = Submission.objects.filter(user=user).distinct("problem").count()
                if total_prob >= self.num_problems:
                    # First submission of each Problem that user have VeredictCode.AC. Ordered by 'creation_date'
                    # Subquery return a list of creation_date of the problems that user submitted a solution
                    order_problem_creation_date = Submission.objects.filter(creation_date__in=Subquery(
                        Submission.objects.filter(user=user).order_by('problem', 'creation_date').distinct('problem').
                        values('creation_date'))).order_by('creation_date').values_list('creation_date', flat=True)
                    new_achi = ObtainedAchievement(user=user,
                                                   obtained_date=order_problem_creation_date[self.num_problems-1],
                                                   achievement_definition=self)
                    new_achi.save()
                    return True
        return False


class Hint(models.Model):
    """Hints of a problem"""
    text_md = models.TextField(max_length=5000, validators=[MinLengthValidator(1)], blank=True)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    num_submit = models.PositiveIntegerField(default=0, null=False)

    def get_text_html(self):
        """Converts a markdown string into HTML"""
        text_html = markdown_to_html(self.text_md, remove_initial_p=True)
        return text_html


class UsedHint(models.Model):
    """Hints used by user"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    request_date = models.DateTimeField(auto_now_add=True)
    hint_definition = models.ForeignKey(Hint, on_delete=models.CASCADE)
