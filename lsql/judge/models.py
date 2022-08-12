# -*- coding: utf-8 -*-
"""
Copyright Enrique Martín <emartinm@ucm.es> 2020

Models to store objects in the DB
"""
from zipfile import ZipFile
import markdown
from lxml import html
from model_utils.managers import InheritanceManager

from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.mail import mail_admins
from django.db import models
from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db.models import JSONField, Subquery
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import translation

from .feedback import compare_select_results, compare_db_results, compare_function_results, compare_discriminant_db
from .oracle_driver import OracleExecutor
from .des_driver import DesExecutor
from .types import VerdictCode, ProblemType, DesMessageType
from .parse import load_select_problem, load_dml_problem, load_function_problem, load_proc_problem, \
    load_trigger_problem, load_discriminant_problem, get_problem_type_from_zip
from .exceptions import ZipFileParsingException, DESException


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
    problems = []
    inner_zipfile = None
    try:
        with ZipFile(file) as zfile:
            for filename in zfile.infolist():
                with zfile.open(filename) as curr_file:
                    inner_zipfile = filename
                    problem = load_problem_from_file(curr_file)
                    problem.clean()
                    problems.append(problem)
                    inner_zipfile = None
    except ZipFileParsingException as excp:
        raise ZipFileParsingException(f'{filename.filename}: {excp}') from excp
    except Exception as excp:
        raise ZipFileParsingException(f'{"" if inner_zipfile is None else inner_zipfile} -> '
                                      f'{type(excp)}: {excp}') from excp
    collection.problems_from_zip = problems


def load_problem_from_file(file):
    """ Load the problem from file using the type in the JSON file """
    problem_types = {ProblemType.SELECT: (SelectProblem, load_select_problem),
                     ProblemType.DML: (DMLProblem, load_dml_problem),
                     ProblemType.FUNCTION: (FunctionProblem, load_function_problem),
                     ProblemType.PROC: (ProcProblem, load_proc_problem),
                     ProblemType.TRIGGER: (TriggerProblem, load_trigger_problem),
                     ProblemType.DISC: (DiscriminantProblem, load_discriminant_problem)}
    problem_type = get_problem_type_from_zip(file)
    prob_class, load_fun = problem_types[problem_type]

    problem = prob_class()
    load_fun(problem, file)
    return problem


def send_des_error_email(excp: Exception, problem_id: int, problem_type: str, create: str, code: str) -> None:
    """ Sends an e-mail to admins with the information of the detected DES error """
    methods = {'SELECT': 'get_des_messages_select',
               'DML': 'get_des_messages_dml'}
    method = methods[problem_type]
    subject = f'Unable to obtain DES output of SELECT problem PK {problem_id}: {excp}'
    msg = f"""Exception {excp}
    
{create}


{code}
----------------------------
----------------------------
Code to replay this error:

from judge.des_driver import DesExecutor
des = DesExecutor.get()
des.{method}('''{create}''', '', '''{code}''')
----------------------------
----------------------------
"""
    mail_admins(subject, msg, fail_silently=True)


class Collection(models.Model):
    """Collection of problems"""
    name_md = models.CharField(max_length=100, validators=[MinLengthValidator(1)])
    name_html = models.CharField(max_length=200, default='', blank=True)
    position = models.PositiveIntegerField(default=1, null=False)
    description_md = models.CharField(max_length=5000, validators=[MinLengthValidator(1)])
    description_html = models.CharField(max_length=10000, default='', blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    creation_date = models.DateTimeField(auto_now_add=True)
    visible = models.BooleanField(default=True)
    # (Dirty) trick to load problems from a ZIP fil by editing a collection using the standard admin interface of Django
    zipfile = models.FileField(upload_to='problem_zips/', default=None, blank=True, null=True)

    def clean(self):
        """ Loads and overwrite data from the ZIP file (if it is set) and creates HTML from markdown """
        try:
            if self.zipfile:
                load_many_problems(self.zipfile, self)
                self.zipfile.close()  # Avoids ResourceWarning in Django storage.py
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
        return self.problem_set.all().order_by('position', 'creation_date')

    def num_problems(self):
        """Number of problems in the collection"""
        return self.problems().count()

    def num_solved_by_user(self, user):
        """Number of problems solved by user in this collection"""
        return Submission.objects.filter(verdict_code='AC', problem__collection=self, user=user) \
            .distinct('problem').count()

    def languages(self):
        """Set with all the languages of the collection"""
        return list(self.problems().order_by('language').distinct('language').values_list('language', flat=True))

    def ranking(self, from_date, to_date, group):
        """ Returns a list of the non-staff users in the group in the order they are in the ranking.
            Each user is extended with the following attributes:
              - n_achievements: number of achievements
              - score: sum of the submissions needed to solve the problems in the collection
              - num_solved: number of problems solved in the collection
              - results: dictionary pk->info of dictionaries with the information for each problem.
                         These inner dictionaries contain:
                    'total_submissions': number of submissions
                    'correct_submissions': number of correct submissions
                    'first_correct_submission': position of the first correct submission (-1 if none)
        """
        users = get_user_model().objects.filter(groups__id=group.id, is_staff=False)
        users_dict = {user.pk: user for user in users}
        for _, user in users_dict.items():
            user.results = {problem.pk: {'total_submissions': 0,
                                         'correct_submissions': 0,
                                         'first_correct_submission': 0}
                            for problem in self.problems()}
            user.n_achievements = len(ObtainedAchievement.objects.filter(user__pk=user.pk))
        submissions = Submission.objects.filter(user__in=users, creation_date__gte=from_date,
                                                creation_date__lte=to_date, problem__collection=self).order_by('pk')
        for submission in submissions:
            # Updates the information of the problem within each submission
            user_pk = submission.user.pk
            problem_pk = submission.problem.pk
            users_dict[user_pk].results[problem_pk]['total_submissions'] += 1
            if (submission.verdict_code == VerdictCode.AC and
                    users_dict[user_pk].results[problem_pk]['correct_submissions'] == 0):
                users_dict[user_pk].results[problem_pk]['first_correct_submission'] = \
                    users_dict[user_pk].results[problem_pk]['total_submissions']
            if submission.verdict_code == VerdictCode.AC:
                users_dict[user_pk].results[problem_pk]['correct_submissions'] += 1

        # Computes num. solved and score from problem statistics
        for _, user in users_dict.items():
            user.num_solved = len([True for info in user.results.values() if info['first_correct_submission'] > 0])
            user.score = sum(info['first_correct_submission'] for info in user.results.values())

        # Sorts users by descending number of solved problems and then ascending by score.
        ranking = sorted(users_dict.values(), key=lambda user: (-1 * user.num_solved, user.score))
        # Sets positions
        last_scores = (-1, -1)
        last_pos = 0
        for user in ranking:
            if last_scores != (user.num_solved, user.score):
                last_pos += 1
            user.pos = last_pos
            last_scores = (user.num_solved, user.score)

        return ranking


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

    # To query Problem and obtain subclass objects with '.select_subclasses()'
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
        return f'(PK {self.pk}) {self.title_md}'

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
        return Submission.objects.filter(user=user, problem=self, verdict_code=VerdictCode.AC).count() > 0

    def num_submissions_by_user(self, user):
        """Number of user submissions to the problem"""
        return Submission.objects.filter(problem=self, user=user).count()

    def solved_n_position(self, position):
        """User (non-staff and active) who solved the problem in 'position' position"""
        active_students = get_user_model().objects.filter(is_staff=False, is_active=True)
        pks = Submission.objects.filter(problem=self, verdict_code=VerdictCode.AC, user__in=active_students) \
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
                        filter(problem=self, user__in=active_students, verdict_code=VerdictCode.AC).
                        order_by('pk', 'user').
                        distinct('pk', 'user').
                        values_list('user', flat=True))
            for users in users_ac:
                if users == user.pk:
                    return iterator
                iterator = iterator + 1
        return None

    def insert_sql_list(self):
        """ List containing all sql inserts """
        return self.insert_sql.split(self.__INSERT_SEPARATION)


class SelectProblem(Problem):
    """Problem that requires a SELECT statement as solution"""
    check_order = models.BooleanField(default=False)
    solution = models.TextField(max_length=5000, validators=[MinLengthValidator(1)], blank=True)
    expected_result = JSONField(encoder=DjangoJSONEncoder, default=None, blank=True, null=True)

    class Meta:
        """ Changes the name displayed in the admin interface"""
        verbose_name_plural = 'Problem_Select'

    def clean(self):
        """ Executes the problem and stores the expected result """
        try:
            if self.zipfile:
                # Replaces the fields with the information from the file
                load_select_problem(self, self.zipfile)
                self.zipfile.close()  # Avoids ResourceWarning in Django storage.py
                self.zipfile = None  # Avoids storing the file in the filesystem
            super().clean()
            self.expected_result = []
            self.initial_db = []
            executor = OracleExecutor.get()
            for insert_sql in self.insert_sql_list():
                res = executor.execute_select_test(self.create_sql, insert_sql,
                                                   self.solution, output_db=True)
                self.expected_result.append(res['result'])
                self.initial_db.append(res['db'])
            # self.validate_des(DesMessageType.ERROR)  # DES validation of new problems is disabled
        except Exception as excp:
            raise ValidationError(excp) from excp

    def template(self):
        return 'problem_select.html'

    def judge(self, code, executor):
        first_insert_sql = self.insert_sql_list()[0]
        oracle_result = executor.execute_select_test(self.create_sql, first_insert_sql, code, output_db=False)
        # Check first code with first db
        verdict, feedback = compare_select_results(self.expected_result[0], oracle_result['result'], self.check_order)
        if verdict != VerdictCode.AC:
            return verdict, feedback
        # Get results using secondary dbs
        insert_sql_extra_list = self.insert_sql_list()[1:]
        initial_db_count = 1
        for insert_sql_extra in insert_sql_extra_list:
            oracle_result_extra = executor.execute_select_test(self.create_sql, insert_sql_extra, code, output_db=False)
            # Check secondary results
            verdict_extra, feedback_extra = compare_select_results(self.expected_result[initial_db_count],
                                                                   oracle_result_extra['result'],
                                                                   self.check_order,
                                                                   self.initial_db[initial_db_count])
            if verdict_extra != VerdictCode.AC:
                return verdict_extra, feedback_extra
            initial_db_count += 1
        # If all results are correct then return the first one
        return verdict, feedback

    def problem_type(self):
        return ProblemType.SELECT

    def get_des_messages(self):
        """ Return a list [DES_messages] **for every test data base**. A DES_messages object is a
            list of pairs (statement, [DES message]) or None"""
        des = DesExecutor.get()
        des_messages = []
        for insert in self.insert_sql_list():
            des_messages.append(des.get_des_messages_select(self.create_sql, insert, self.solution))
        return des_messages

    def get_des_messages_solution(self, code):
        """ Return a flat list of DES messages obtained for the user code """
        des = DesExecutor.get()
        # Checks DES only with the first DB
        try:
            des_messages = des.get_des_messages_select(self.create_sql, '', code)  # INSERT are not needed
        except DESException as excp:
            send_des_error_email(excp, self.pk, 'SELECT', str(self.create_sql), code)
            return []
        messages = [(msg_type, msg, snippet) for _, msgs in des_messages
                    for msg_type, msg, snippet in msgs if msgs]
        return messages

    def validate_des(self, min_level=DesMessageType.ERROR):
        """ Validates that the current problem does not generate any error message with
            level smaller than 'level' (by default ERROR) """
        des_messages = self.get_des_messages()
        for bd_msgs in des_messages:
            for stmt, msg_list in bd_msgs:
                for des_level, text, stmt_snippet in msg_list:
                    if des_level <= min_level:
                        error_msg = f'DES Validation error in <{stmt}>. Error code: {des_level}. ' \
                                    f'Error message: {text}. Snippet: {stmt_snippet}'
                        raise ValidationError(error_msg)


class DMLProblem(Problem):
    """Problem that requires one or more DML statements (INSERT, UPDATE, CREATE...) as solution"""
    # IMPORTANT: This problem does not support multiple initial db. It only uses the first db
    check_order = models.BooleanField(default=False)
    solution = models.TextField(max_length=5000, validators=[MinLengthValidator(1)], blank=True)
    expected_result = JSONField(encoder=DjangoJSONEncoder, blank=True)

    class Meta:
        """ Changes the name displayed in the admin interface"""
        verbose_name_plural = 'Problem_DML'

    def clean(self):
        """Executes the problem and stores the expected result"""
        try:
            if self.zipfile:
                # Replaces the fields with the information from the file
                load_dml_problem(self, self.zipfile)
                self.zipfile.close()  # Avoids ResourceWarning in Django storage.py
                self.zipfile = None  # Avoids storing the file in the filesystem

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

    def get_des_messages(self):
        """ Return a list [DES_messages] **for every test data base**. A DES_messages object is a
            list of pairs (statement, [DES message]) or None"""
        des = DesExecutor.get()
        des_messages = []
        for insert in self.insert_sql_list():
            des_messages.append(des.get_des_messages_dml(self.create_sql, insert, self.solution))
        return des_messages

    def get_des_messages_solution(self, code):
        """ Return a flat list of DES messages obtained for the user code """
        des = DesExecutor.get()
        # Checks DES only with the first DB
        try:
            des_messages = des.get_des_messages_dml(self.create_sql, self.insert_sql_list()[0], code)
            # Needed because DES generate "No tuple met the 'where' condition for updating" if omitted
        except DESException as excp:
            send_des_error_email(excp, self.pk, 'DML', str(self.create_sql), code)
            return []
        # Uses the whole statement as snippet because:
        # A) DES doesn't seem to provide detailed snippets for DML errors
        # B) DML problems can have several statements, so messages without context are difficult to understand
        messages = [(msg_type, msg, stmt.strip()) for stmt, msgs in des_messages
                    for msg_type, msg, snippet in msgs if msgs]
        return messages

    def validate_des(self, min_level=DesMessageType.ERROR):
        """ Validates that the current problem does not generate any error message with
            level smaller than 'level' (by default ERROR). If some message is found,
            raises a ValidationError with that first message
        """
        des_messages = self.get_des_messages()
        for bd_msgs in des_messages:
            for stmt, msg_list in bd_msgs:
                for des_level, text, stmt_snippet in msg_list:
                    if des_level <= min_level:
                        error_msg = f'DES Validation error in <{stmt.strip()}>. Error code: {des_level}. ' \
                                    f'Error message: {text}. Snippet: {stmt_snippet}'
                        raise ValidationError(error_msg)


class FunctionProblem(Problem):
    """Problem that requires a function definition as solution"""
    # IMPORTANT: This problem does not support multiple initial db. It only uses the first db
    check_order = models.BooleanField(default=False)
    solution = models.TextField(max_length=5000, validators=[MinLengthValidator(1)], blank=True)
    calls = models.TextField(max_length=5000, validators=[MinLengthValidator(1)], default='', blank=True)
    expected_result = JSONField(encoder=DjangoJSONEncoder, blank=True)

    class Meta:
        """ Changes the name displayed in the admin interface"""
        verbose_name_plural = 'Problem_Function'

    def clean(self):
        """Executes the problem and stores the expected result"""
        try:
            if self.zipfile:
                # Replaces the fields with the information from the file
                load_function_problem(self, self.zipfile)
                self.zipfile.close()  # Avoids ResourceWarning in Django storage.py
                self.zipfile = None  # Avoids storing the file in the filesystem

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
        rows = [[call, result[0]] for call, result in self.expected_result[0].items()]
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

    class Meta:
        """ Changes the name displayed in the admin interface"""
        verbose_name_plural = 'Problem_Procedure'

    def template(self):
        return 'problem_proc.html'

    def clean(self):
        """Executes the problem and stores the expected result"""
        try:
            if self.zipfile:
                # Replaces the fields with the information from the file
                load_proc_problem(self, self.zipfile)
                self.zipfile.close()  # Avoids ResourceWarning in Django storage.py
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

    class Meta:
        """ Changes the name displayed in the admin interface"""
        verbose_name_plural = 'Problem_Trigger'

    def template(self):
        return 'problem_trigger.html'  # The same template works

    def clean(self):
        """Executes the problem and stores the expected result"""
        try:
            if self.zipfile:
                # Replaces the fields with the information from the file
                load_trigger_problem(self, self.zipfile)
                self.zipfile.close()  # Avoids ResourceWarning in Django storage.py
                self.zipfile = None  # Avoids storing the file in the filesystem

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

    class Meta:
        """ Changes the name displayed in the admin interface"""
        verbose_name_plural = 'Problem_Discriminant'

    def template(self):
        return 'problem_disc.html'

    def clean(self):
        """Executes the problem and stores the expected result"""
        try:
            if self.zipfile:
                # Replaces the fields with the information from the file
                load_discriminant_problem(self, self.zipfile)
                self.zipfile.close()  # Avoids ResourceWarning in Django storage.py
                self.zipfile = None  # Avoids storing the file in the filesystem

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
    verdict_code = models.CharField(
        max_length=3,
        choices=VerdictCode.choices,
        default=VerdictCode.AC
    )
    verdict_message = models.CharField(max_length=5000, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.pk} - {self.user.email} - {self.verdict_code}"

    def verdict_html_name(self):
        """ Returns the HTML code with the verdict name in colors """
        return VerdictCode(self.verdict_code).html_short_name()


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
    obtained_date = models.DateTimeField(default=timezone.now)
    achievement_definition = models.ForeignKey(AchievementDefinition, on_delete=models.CASCADE)

    class Meta:
        """ Changes the name displayed in the admin interface"""
        verbose_name_plural = 'Achievement_Obtained'


class NumSolvedAchievementDefinition(AchievementDefinition, models.Model):
    """Achievement by solving a number of problems"""
    num_problems = models.PositiveIntegerField(default=1, null=False)

    class Meta:
        """ Changes the name displayed in the admin interface"""
        verbose_name_plural = 'AchievementDef_NumSolved'

    def check_and_save(self, user):
        """Return if an user is deserving for get an achievement, if it is, save that"""
        if not self.check_user(user):
            corrects = Submission.objects.filter(verdict_code=VerdictCode.AC, user=user).distinct("problem").count()
            if corrects >= self.num_problems:
                # First submission of each Problem that user have VerdictCode.AC. Ordered by 'creation_date'
                # Subquery return a list of creation_date of the problems that user have VerdictCode.AC
                order_problem_creation_date = Submission.objects.filter(creation_date__in=Subquery(
                    Submission.objects.filter(verdict_code=VerdictCode.AC, user=user).
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

    class Meta:
        """ Changes the name displayed in the admin interface"""
        verbose_name_plural = 'AchievementDef_Podium'

    def check_and_save(self, user):
        """Return if an user is deserving for get an achievement, if it is, save that"""
        if not self.check_user(user):
            # First submission of each Problem that user have VerdictCode.AC. Ordered by 'creation_date'
            # Subquery return a list of creation_date of the problems that user have VerdictCode.AC
            order_problem_creation_date = Submission.objects.filter(creation_date__in=Subquery(
                Submission.objects.filter(verdict_code=VerdictCode.AC, user=user).
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

    class Meta:
        """ Changes the name displayed in the admin interface"""
        verbose_name_plural = 'AchievementDef_NumSolvedCollection'

    def check_and_save(self, user):
        """Return if an user is deserving for get an achievement, if it is, save that"""
        if not self.check_user(user):
            corrects = Submission.objects.filter(verdict_code=VerdictCode.AC, user=user,
                                                 problem__collection=self.collection).distinct("problem").count()
            if corrects >= self.num_problems:
                # First submission of each Problem that user have VerdictCode.AC. Ordered by 'creation_date'
                # Subquery return a list of creation_date of the problems that user have VerdictCode.AC
                order_problem_creation_date = Submission.objects.filter(creation_date__in=Subquery(
                    Submission.objects.filter(verdict_code=VerdictCode.AC, user=user,
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

    class Meta:
        """ Changes the name displayed in the admin interface"""
        verbose_name_plural = 'AchievementDef_NumSolvedType'

    def check_and_save(self, user):
        """Return if an user is deserving for get an achievement, if it is, save that"""
        if not self.check_user(user):
            count = 0
            # First submission of each Problem that user have VerdictCode.AC. Ordered by 'creation_date'
            # Subquery return a list of creation_date of the problems that user have VerdictCode.AC
            order_problem_creation_date = Submission.objects.filter(creation_date__in=Subquery(
                Submission.objects.filter(verdict_code=VerdictCode.AC, user=user).
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

    class Meta:
        """ Changes the name displayed in the admin interface"""
        verbose_name_plural = 'AchievementDef_NumSubmissions'

    def check_and_save(self, user):
        """Return if an user is deserving for get an achievement, if it is, save that"""
        if not self.check_user(user):
            total_submissions = Submission.objects.filter(user=user).count()
            if total_submissions >= self.num_submissions:
                total_prob = Submission.objects.filter(user=user).distinct("problem").count()
                if total_prob >= self.num_problems:
                    # First submission of each Problem that user have VerdictCode.AC. Ordered by 'creation_date'
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

    class Meta:
        """ Changes the name displayed in the admin interface"""
        verbose_name_plural = 'Hint_definition'

    def get_text_html(self):
        """Converts a markdown string into HTML"""
        text_html = markdown_to_html(self.text_md, remove_initial_p=True)
        return text_html

    def __str__(self): # pragma: no cover
        """ String representation of Hint object """
        return f'Hint #{self.pk} - problem {self.problem}'


class UsedHint(models.Model):
    """Hints used by user"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    request_date = models.DateTimeField(auto_now_add=True)
    hint_definition = models.ForeignKey(Hint, on_delete=models.CASCADE)

    class Meta:
        """ Changes the name displayed in the admin interface"""
        verbose_name_plural = 'Hint_Used'

    def __str__(self): # pragma: no cover
        """ String representation of used Hint object """
        return f'UsedHint (PK {self.pk})'
