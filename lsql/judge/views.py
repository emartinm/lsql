# -*- coding: utf-8 -*-
"""
Copyright Enrique Martín <emartinm@ucm.es> 2020
Functions that process HTTP connections
"""
from datetime import timedelta, datetime
import io

from logzero import logger
from pyexcel_ods3 import save_data

from django.http import HttpResponseRedirect, JsonResponse, HttpResponseForbidden, FileResponse
from django.http.response import HttpResponse, HttpResponseNotFound
from django.urls import reverse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _, ngettext, gettext
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from django.template.exceptions import TemplateDoesNotExist
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from .exceptions import ExecutorException
from .feedback import compile_error_to_html_table, filter_expected_db
from .forms import SubmitForm, ResultStaffForm, ResultStudentForm, ShowSubmissionsForm, DownloadRankingForm
from .models import Collection, Problem, Submission, ObtainedAchievement, AchievementDefinition, \
    NumSubmissionsProblemsAchievementDefinition, Hint, UsedHint
from .oracle_driver import OracleExecutor
from .types import VerdictCode, OracleStatusCode, ProblemType
from .statistics import submissions_by_day, submission_count, participation_per_group

# TRANSLATIONS #
# To translate the code to another language you need to create the translation file:
# 1) $ django-admin makemessages -l en
#    where "en" is the English language code.
# 2) Complete the msgstr in lsql/locale/en/LC_MESSAGES/django.po with the new translations.
# 3) $ django-admin compilemessages
#
# If the msgstr is empty, it will use the msgid instead. 2) Use these commands everytime you add a new translation
# outside the translation file. It won't remove existing translations.
# FOR WINDOWS: https://mlocati.github.io/articles/gettext-iconv-windows.html is necessary to execute the commands.


####################
# Helper functions #
####################

def get_subclass_problem(problem_id):
    """Look for problem 'pk' in the different child classes of Problem"""
    queryset = Problem.objects.filter(pk=problem_id).select_subclasses()
    return None if len(queryset) == 0 else queryset[0]


def first_day_of_course(init_course):
    """ Returns the first day of the academic year """
    first_day = datetime(init_course.year, 9, 1)
    if 1 <= init_course.month < 9:
        first_day = datetime(init_course.year - 1, 9, 1)
    return first_day


def check_if_get_achievement(user, verdict):
    """Check if the user get some achievement and return a list of obtained achievements"""
    obtained_achievements = []
    if verdict == VerdictCode.AC:
        for ach in AchievementDefinition.objects.all().select_subclasses():
            if ach.check_and_save(user):
                obtained_achievements.append(ach)

    # If the verdict != AC (correct) only can get a NumSubmissionsProblemsAchievementDefinition
    else:
        for ach in NumSubmissionsProblemsAchievementDefinition.objects.all():
            if ach.check_and_save(user):
                obtained_achievements.append(ach)

    return obtained_achievements


##############
#   Views    #
##############

def index(_):
    """Redirect root access to collections"""
    return HttpResponseRedirect(reverse('judge:collections'))


@login_required
def help_page(request):
    """ Shows help page """
    try:
        return render(request, 'help.'+ request.LANGUAGE_CODE + '.html')
    except TemplateDoesNotExist:
        return render(request, 'help.'+ settings.LANGUAGE_CODE + '.html')


@login_required
def show_result(request, collection_id):
    """ Show the ranking of a group (GET param) for collection_id """
    if not Group.objects.all():
        # Show an informative message if there are not groups in the system
        return render(request, 'generic_error_message.html',
                      {'error': [_('¡Lo sentimos! No existe ningún grupo para ver resultados')]})
    collection = get_object_or_404(Collection, pk=collection_id)
    result_staff_form = ResultStaffForm(request.GET)
    result_student_form = ResultStudentForm(request.GET)

    if request.user.is_staff and result_staff_form.is_valid():
        group_id = result_staff_form.cleaned_data['group']
        group = get_object_or_404(Group, pk=group_id)
        start = result_staff_form.cleaned_data.get('start')
        end = result_staff_form.cleaned_data.get('end')
        user_groups = Group.objects.all().order_by('name')
    elif not request.user.is_staff and result_student_form.is_valid():
        user_groups = request.user.groups.all().order_by('name')
        group_id = result_student_form.cleaned_data['group']
        group = get_object_or_404(Group, pk=group_id)
        if group not in user_groups:
            return HttpResponseForbidden("Forbidden")
        start, end = None, None
    elif request.user.is_staff and not result_staff_form.is_valid():
        # Error 404 with all the validation errors as HTML
        return HttpResponseNotFound(str(result_staff_form.errors))
    elif not result_student_form.is_valid():
        # Error 404 with all the validation errors as HTML
        return HttpResponseNotFound(str(result_student_form.errors))

    # Set start and end if they were not provided
    start = first_day_of_course(datetime.today()) if start is None else start
    end = datetime.today() if end is None else end
    # Extends 'end' to 23:59:59 to cover today's latest submissions. Otherwise, ranking is not
    # updated until next day (as plain dates have time 00:00:00)
    end = datetime(end.year, end.month, end.day, 23, 59, 59)

    ranking = collection.ranking(start, end, group)
    return render(request, 'results.html', {'collection': collection, 'groups': user_groups,
                                            'current_group': group,
                                            'end_date': end, 'start_date': start,
                                            'ranking': ranking})


@login_required
def show_results(request):
    """ Shows the links to enter the results of each collection """
    if not Group.objects.all():
        # Show an informative message if there are not groups in the system
        return render(request, 'generic_error_message.html',
                      {'error': [_('¡Lo sentimos! No existe ningún grupo para ver resultados')]})

    cols = Collection.objects.all().order_by('position', '-creation_date')
    groups_user = request.user.groups.all().order_by('name')
    if groups_user.count() == 0 and not request.user.is_staff:
        return render(request, 'generic_error_message.html',
                      {'error': [_('¡Lo sentimos! No tienes asignado un grupo de la asignatura.'),
                                 _('Por favor, contacta con tu profesor para te asignen un grupo de clase.')]
                       })
    if groups_user.count() == 0 and request.user.is_staff:
        groups_user = Group.objects.all().order_by('name')

    return render(request, 'result.html', {'user': request.user, 'results': cols, 'group': groups_user[0].id})


@login_required
def show_collections(request):
    """Show all the collections"""
    cols = Collection.objects.all().order_by('position', '-creation_date')
    for collection in cols:
        # Templates can only invoke nullary functions or access object attribute, so we store
        # the number of problems solved by the user in an attribute
        collection.num_solved = collection.num_solved_by_user(request.user)
    return render(request, 'collections.html', {'collections': cols})


@login_required
def show_collection(request, collection_id):
    """Shows a collection"""
    collection = get_object_or_404(Collection, pk=collection_id)
    # New attribute to store the list of problems and include the number of submission in each problem
    collection.problem_list = collection.problems()
    for problem in collection.problem_list:
        problem.num_submissions = problem.num_submissions_by_user(request.user)
        problem.solved = problem.solved_by_user(request.user)
    return render(request, 'collection.html', {'collection': collection})


@login_required
def show_problem(request, problem_id):
    """Shows a concrete problem"""
    # Error 404 if there is no a Problem pk
    get_object_or_404(Problem, pk=problem_id)
    # Look for problem pk in all the Problem classes
    problem = get_subclass_problem(problem_id)
    # Stores the flag in an attribute so that the template can use it
    problem.solved = problem.solved_by_user(request.user)
    # Filter the expected result to display it
    problem.show_added, problem.show_modified, problem.show_removed = filter_expected_db(problem.expected_result[0],
                                                                                         problem.initial_db[0])
    problem.available_hints = Hint.objects.filter(problem=problem).order_by('num_submit').count()
    used_hints = UsedHint.objects.filter(user=request.user).filter(hint_definition__problem=problem)
    hints = []
    cont = 0
    for used in used_hints:
        cont += 1
        name = _('Pista {number}').format(number=cont)
        dic = {'num':  name, 'text_html': used.hint_definition.get_text_html()}
        hints.append(dic)
    problem.used_hints = hints
    problem.used = len(hints)
    return render(request, problem.template(), {'problem': problem})


@login_required
def show_submissions(request):
    """ Shows all the submissions of one user, for some problem in a time window. Staff member
        can see any submission, students only their own.
    """
    form = ShowSubmissionsForm(request.GET)
    if form.is_valid():
        problem_id = form.cleaned_data.get('problem_id')
        problem = get_object_or_404(Problem, pk=problem_id) if problem_id is not None else None
        user_id = form.cleaned_data.get('user_id')
        user = get_object_or_404(get_user_model(), id=user_id) if user_id is not None else request.user
        if not request.user.is_staff and user != request.user:
            return HttpResponseForbidden("Forbidden")
        first_submission_date = datetime(1950, 1, 1)
        start = form.cleaned_data.get('start') if form.cleaned_data.get('start') is not None \
            else first_submission_date
        end = form.cleaned_data.get('end') if form.cleaned_data.get('end') is not None \
            else datetime.today()
        if problem is not None:
            subs = Submission.objects.filter(user=user, problem=problem.id,
                                             creation_date__range=[start, end + timedelta(days=1)]).order_by('-pk')
        else:
            subs = Submission.objects.filter(user=user,
                                             creation_date__range=[start, end + timedelta(days=1)]).order_by('-pk')
    else:
        return HttpResponseNotFound(str(form.errors))
    return render(request, 'submissions.html', {'submissions': subs, 'user': user})


@login_required
def show_achievements(request, user_id):
    """View for show the achievements"""
    this_user = get_user_model().objects.get(pk=user_id)
    achievements_locked = []
    achievements_unlocked = ObtainedAchievement.objects.filter(user=this_user)
    achievements_definitions_unlocked = ObtainedAchievement.objects.filter(user=this_user).\
        values_list('achievement_definition', flat=True)
    all_achievements_definitions = AchievementDefinition.objects.values_list('pk', flat=True)
    achievements_locked_pk = all_achievements_definitions.difference(achievements_definitions_unlocked)
    for identifier in achievements_locked_pk:
        ach = AchievementDefinition.objects.get(pk=identifier)
        achievements_locked.append(ach)
    return render(request, 'achievements.html', {'locked': achievements_locked,
                                                 'unlocked': achievements_unlocked,
                                                 'username': this_user.username})


@login_required
def show_hints(request):
    """View for show the used hints"""
    context = {'user': request.user, 'elements': {}}
    dic = {}
    hints = UsedHint.objects.filter(user=request.user.pk).order_by('request_date')
    for hint in hints:
        if hint.hint_definition.problem.pk in dic:
            dic[hint.hint_definition.problem.pk].append(hint)
        else:
            dic[hint.hint_definition.problem.pk] = [hint]
    context['elements'] = dic
    return render(request, 'hints.html', context)


@login_required
def show_submission(request, submission_id):
    """Shows a submission of the current user"""
    submission = get_object_or_404(Submission, pk=submission_id)
    if submission.user != request.user and not request.user.is_staff:
        return HttpResponseForbidden("Forbidden")
    submission.verdict_pretty = VerdictCode(submission.verdict_code).html_short_name()
    return render(request, 'submission.html', {'submission': submission})


@login_required
def download_submission(request, submission_id):
    """ Return a script with te code of submission """
    submission = get_object_or_404(Submission, pk=submission_id)
    if submission.user != request.user and not request.user.is_staff:
        return HttpResponseForbidden("Forbidden")
    response = HttpResponse()
    response['Content-Type'] = 'application/sql'
    response['Content-Disposition'] = "attachment; filename=code.sql"
    response.write(submission.code)
    return response


@login_required
def download(_, problem_id):
    """Returns a script with the creation and insertion of the problem"""
    get_object_or_404(Problem, pk=problem_id)
    # Look for problem pk in all the Problem classes
    problem = get_subclass_problem(problem_id)
    response = HttpResponse()
    response['Content-Type'] = 'application/sql'
    response['Content-Disposition'] = "attachment; filename=create_insert.sql"
    response.write(problem.create_sql + '\n\n' + problem.insert_sql)
    return response


def extend_dictionary_with_des(data, problem, code):
    """ Extend the data that answers a submission with DES feedback (if needed) """
    if problem.problem_type() == ProblemType.SELECT:
        messages_raw = problem.get_des_messages_solution(code)
        # Extends the snippet to mark the position of the error and also extract line and column
        messages = list()
        for (error_code, msg, snippet) in messages_raw:
            if snippet:
                len_last_line = len(snippet.strip().split('\n')[-1])
                num_line = len(snippet.strip().split('\n'))
                snippet += '.'*len_last_line + '^^^'
                line_col = (num_line, len_last_line)
            else:
                line_col = None
            messages.append((error_code, msg, snippet, line_col))
        # We strip to avoid submitting empty strings
        data['des'] = render_to_string('feedback_des.html', {'des_msgs': messages}).strip()


@login_required
# pylint does not understand the dynamic attributes in VerdictCode (TextChoices), so we need to disable
# no-member warning in this specific function
# pylint: disable=no-member
def submit(request, problem_id):
    """Process a user submission"""
    # Error 404 if there is no Problem 'pk'
    general_problem = get_object_or_404(Problem, pk=problem_id)
    problem = get_subclass_problem(problem_id)
    submit_form = SubmitForm(request.POST)
    data = {'verdict': VerdictCode.IE, 'title': VerdictCode.IE.label,
            'message': VerdictCode.IE.message(), 'feedback': '', 'des': ''}
    code = ''
    if submit_form.is_valid():
        try:
            # AC or WA
            code = submit_form.cleaned_data['code']
            data['verdict'], data['feedback'] = problem.judge(code, OracleExecutor.get())
            data['title'] = data['verdict'].label
            data['message'] = data['verdict'].message()
            extend_dictionary_with_des(data, problem, code)  # Check DES if needed
        except ExecutorException as excp:
            # Exceptions when judging: RE, TLE, VE or IE
            if excp.error_code == OracleStatusCode.EXECUTE_USER_CODE:
                data['verdict'] = VerdictCode.RE
                data['title'] = VerdictCode.RE.label
                data['message'] = VerdictCode.RE.message()
                data['feedback'] = (f'{excp.statement} --> {excp.message}'
                                    if problem.problem_type() == ProblemType.FUNCTION else excp.message)
                data['position'] = excp.position
                data['position_msg'] = _('Posición: línea {row}, columna {col}')\
                    .format(row=excp.position[0]+1, col=excp.position[1]+1)
                extend_dictionary_with_des(data, problem, code)  # Check DES if needed
            elif excp.error_code == OracleStatusCode.TLE_USER_CODE:
                data['verdict'] = VerdictCode.TLE
                data['title'] = VerdictCode.TLE.label
                data['message'] = VerdictCode.TLE.message()
                extend_dictionary_with_des(data, problem, code)  # Check DES if needed
            elif excp.error_code == OracleStatusCode.NUMBER_STATEMENTS:
                data['verdict'] = VerdictCode.VE
                data['title'] = VerdictCode.VE.label
                data['message'] = VerdictCode.VE.message(problem)
                data['feedback'] = excp.message
            elif excp.error_code == OracleStatusCode.COMPILATION_ERROR:
                data['verdict'] = VerdictCode.WA
                data['title'] = VerdictCode.WA.label
                data['message'] = VerdictCode.WA.message()
                data['feedback'] = compile_error_to_html_table(excp.message)
    else:
        data['verdict'] = VerdictCode.VE
        data['title'] = VerdictCode.VE.label
        data['message'] = VerdictCode.VE.message()

    submission = Submission(code=code, verdict_code=data['verdict'], verdict_message=data['message'],
                            user=request.user, problem=general_problem)
    submission.save()
    # If verdict is correct look for an achievement to complete if it's possible
    achieve_list = check_if_get_achievement(request.user, data['verdict'])

    if achieve_list:
        if len(achieve_list) == 1:
            sentence = _("Además, con este envío has conseguido el logro ")
        else:
            sentence = _("Además, con este envío has conseguido los logros ")
        context = {'achieve': achieve_list, 'user': request.user.pk, 'sentence': sentence}
        html = render_to_string('achievement_notice.html', context)
        data['achievements'] = html
    logger.debug('Stored submission %s', submission)
    return JsonResponse(data)


@login_required
def password_change_done(request):
    """Password change confirmation"""
    return render(request, 'password_change_done.html')


def test_error_500(request):
    """Generates a server internal error, only for testing error reporting in deployment"""
    if request.user and request.user.is_staff:
        elems = list()
        return HttpResponse(elems[55])  # list index out of range, error 500
    return HttpResponseNotFound()


def cell_ranking(problem):
    """ Generates the text inside a ranking cell """
    if problem['correct_submissions'] > 0:
        return "{}/{} ({})".format(problem['correct_submissions'],
                                   problem['total_submissions'],
                                   problem['first_correct_submission'])
    return "{}/{}".format(problem['correct_submissions'],
                          problem['total_submissions'])


@login_required
def download_ranking(request, collection_id):
    """ Download Excel file with the results of submissions """
    collection = get_object_or_404(Collection, pk=collection_id)
    result_form = DownloadRankingForm(request.GET)
    if request.user.is_staff and result_form.is_valid():
        group = get_object_or_404(Group, pk=result_form.cleaned_data['group'])
        start = result_form.cleaned_data.get('start')
        end = result_form.cleaned_data.get('end')
        # Extends 'end' to 23:59:59 to cover today's latest submissions. Otherwise, ranking is not
        # updated until next day (as plain dates have time 00:00:00)
        end = datetime(end.year, end.month, end.day, 23, 59, 59)
        start = datetime(start.year, start.month, start.day, 0, 0, 0)

        sheet_rows = list()
        # Sheet header: collection name, dates and group in first 4 rows
        sheet_rows.append([gettext('Colección'), collection.name_md])
        sheet_rows.append([gettext('Grupo'), str(group)])
        sheet_rows.append([gettext('Desde'), str(start)])
        sheet_rows.append([gettext('Hasta'), str(end)])
        sheet_rows.append([])

        # Table header [Pos., User, Exercises..., Score, Solved] in row 6
        sheet_rows.append([gettext("Pos."), gettext("Usuario")] +
                          [problem.title_md for problem in collection.problems()] +
                          [gettext("Puntuación."), gettext("Resueltos")])
        # Ranking row by row
        for user in collection.ranking(start, end, group):
            sheet_rows.append([user.pos, user.username] +
                              [cell_ranking(problem) for _, problem in user.results.items()] +
                              [user.score, user.num_solved])
        # Saves ODS to memory and includes it in the response
        buffer = io.BytesIO()
        save_data(buffer, {str(group): sheet_rows})
        buffer.seek(0)  # Moves to the beginning of the buffer
        return FileResponse(buffer, as_attachment=True, filename='ranking.ods')
    if request.user.is_staff and not result_form.is_valid():
        return HttpResponseNotFound(str(result_form.errors))
    return HttpResponseForbidden("Forbidden")


@staff_member_required
def statistics_submissions(request):
    """ Shows statistics page containing charts and other summarized information """
    all_submissions_count = submissions_by_day()
    start = all_submissions_count[0][0] if all_submissions_count else None
    end = all_submissions_count[-1][0] if all_submissions_count else None
    ac_submissions = submissions_by_day(start, end, verdict_code=VerdictCode.AC)
    wa_submissions = submissions_by_day(start, end, verdict_code=VerdictCode.WA)
    re_submissions = submissions_by_day(start, end, verdict_code=VerdictCode.RE)
    sub_count = submission_count()
    involved_users = participation_per_group()
    return render(request, 'statistics_submissions.html',
                  {'all_submissions_count': all_submissions_count,
                   'ac_submissions_count': ac_submissions,
                   'wa_submissions_count': wa_submissions,
                   're_submissions_count': re_submissions,
                   'submission_count': sub_count,
                   'participating_users': involved_users})


@login_required
@require_POST
def get_hint(request, problem_id):
    """Returns a JSON with the information of available Hints"""
    problem = get_object_or_404(Problem, pk=problem_id)
    num_subs = Submission.objects.filter(problem=problem, user=request.user).count()
    list_hints = Hint.objects.filter(problem=problem).order_by('num_submit')
    list_used_hints = UsedHint.objects.filter(user=request.user.pk).filter(hint_definition__problem=problem)
    data = {'hint': '', 'msg': '', 'more_hints': False}
    num_hint = list_used_hints.count()

    # if there are not more hints available
    if list_hints.count() == list_used_hints.count():
        data['more_hints'] = False
        data['msg'] = _('No hay más pistas disponibles para este ejercicio.')
    else:
        hint = list_hints[num_hint]

        # if the number of wrong submission is less than the number of submissions
        if num_subs >= hint.num_submit:
            hint_number = list_used_hints.count() + 1
            context = {'hint_number': hint_number, 'text': hint.get_text_html()}
            html = render_to_string('hint.html', context)
            data['hint'] = html
            used_hint = UsedHint(user=request.user, hint_definition=hint)
            used_hint.save()
            if list_hints.count() == list_used_hints.count():
                data['more_hints'] = False
                data['msg'] = _('No hay más pistas disponibles para este ejercicio.')
            else:
                data['more_hints'] = True
        else:
            num = hint.num_submit - num_subs
            data['more_hints'] = True
            data['msg'] = ngettext(
                'Te falta %(num)d envío para desbloquear la siguiente pista',
                'Te faltan %(num)d envíos para desbloquear la siguiente pista',
                num,
            ) % {'num': num}

    return JsonResponse(data)
