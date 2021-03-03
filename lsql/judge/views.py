# -*- coding: utf-8 -*-
"""
Copyright Enrique Martín <emartinm@ucm.es> 2020
Functions that process HTTP connections
"""
import datetime
from datetime import timedelta
from django.http import HttpResponseRedirect, JsonResponse, HttpResponseForbidden
from django.http.response import HttpResponse, HttpResponseNotFound
from django.urls import reverse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required
from logzero import logger
from .exceptions import ExecutorException
from .feedback import compile_error_to_html_table
from .forms import SubmitForm
from .models import Collection, Problem, SelectProblem, DMLProblem, ProcProblem, FunctionProblem, TriggerProblem, \
    Submission
from .oracle_driver import OracleExecutor
from .types import VeredictCode, OracleStatusCode, ProblemType


def get_child_problem(problem_id):
    """Look for problem 'pk' in the different child classes of Problem"""
    classes = [SelectProblem, DMLProblem, FunctionProblem, ProcProblem, TriggerProblem]
    i = 0
    problem = None
    while i < len(classes) and problem is None:
        problems = classes[i].objects.filter(pk=problem_id)
        i += 1
        if problems:
            problem = problems[0]
    return problem


def pos(user_1, user_2):
    """compare if user_1 has a better ranking than user_2"""
    if user_1.resolved == user_2.resolved and user_1.score == user_2.score:
        return False
    return True


def index(_):
    """Redirect root access to collections"""
    return HttpResponseRedirect(reverse('judge:collections'))


def firstDayOfCourse():
    """Returned on the first day of the academic year"""
    if 1 <= datetime.datetime.today().month < 9:
        return datetime.datetime(datetime.datetime.today().year-1, 9, 1).strftime('%Y-%m-%d')
    return datetime.datetime(datetime.datetime.today().year, 9, 1).strftime('%Y-%m-%d')


def for_loop(user_logged, user, collection, start, end):
    """From each exercise of the collection assigns the attempts and success for each user"""
    for numb in range(0, collection.problem_list.count()):
        num_accepted = 0
        enter = False
        attempts = 0
        problem = collection.problem_list[numb]
        user.first_AC = 0
        if user_logged.is_staff:
            starts = datetime.datetime.strptime(start, '%Y-%m-%d')
            ends = datetime.datetime.strptime(end, '%Y-%m-%d')
            subs = Submission.objects.filter(user=user,
                                             problem=problem.id,
                                             creation_date__range=[starts, ends + timedelta(days=1)]).order_by('pk')

        else:
            subs = Submission.objects.filter(user=user).filter(problem=problem.id).order_by('pk')
        length = len(subs)
        for submission in range(0, length):
            if subs[submission].veredict_code == VeredictCode.AC:
                num_accepted = num_accepted + 1
            if num_accepted == 1 and not enter:
                enter = True
                user.first_AC = submission + 1
                user.score = user.score + submission + 1
            attempts = attempts + 1

        solved(attempts, user, problem, num_accepted, collection, numb, enter)


def solved(attempts, user, problem, num_accepted, collection, numb, enter):
    """Adds the problem to the user's collection and assigns the number of submissions"""
    if attempts > 0 and user.first_AC == 0:
        problem.num_submissions = f"{num_accepted}/{attempts} ({attempts})"
        problem.solved = False
    else:
        problem.num_submissions = f"{num_accepted}/{attempts} ({user.first_AC})"
        problem.solved = collection.problem_list[numb].solved_by_user(user)
    if problem.solved and enter:
        user.resolved = user.resolved + 1
    user.collection.append(problem)


@login_required
def show_result(request, collection_id):
    """show datatable of a group"""
    if not Group.objects.all():
        # Show an informative message if there are not groups in the system
        return render(request, 'generic_error_message.html',
                      {'error': ['¡Lo sentimos! No se han configurado grupos configurados en el juez para ver '
                                 'resultados']})
    position = 1
    try:
        start = request.GET.get('start')
        end = request.GET.get('end')
        group_id = request.GET.get('group')
        print(start)
        up_to_classification_date = None
        from_classification_date = None
        collection = get_object_or_404(Collection, pk=collection_id)
        if request.user.is_staff:
            groups_user = Group.objects.all().order_by('name')
            up_to_classification_date = datetime.datetime.strptime(end, '%Y-%m-%d')
            from_classification_date = datetime.datetime.strptime(start, '%Y-%m-%d')
        else:
            if start is not None or end is not None:
                return HttpResponseForbidden("Forbidden")
            groups_user = request.user.groups.all().order_by('name')
        if group_id is None:
            group_id = groups_user[0].id
        group0 = get_object_or_404(Group, pk=group_id)
        users = get_user_model().objects.filter(groups__name=group0.name)
        if users.filter(id=request.user.id) or request.user.is_staff:
            group0.name = group0.name
            group0.id = group_id
            groups_user = groups_user.exclude(id=group_id)
            collection.problem_list = collection.problems()
            collection.total_problem = collection.problem_list.count()
            users = users.exclude(is_staff=True)
            for user in users:
                user.collection = []
                user.resolved = 0
                user.score = 0
                for_loop(request.user, user, collection, start, end)
            users = sorted(users, key=lambda x: (x.resolved, -x.score), reverse=True)
            length = len(users)
            for i in range(0, length):
                if i != len(users) - 1:
                    if pos(users[i], users[i + 1]):
                        users[i].pos = position
                        position = position + 1
                    else:
                        users[i].pos = position
                else:
                    if pos(users[i], users[i - 1]):
                        users[i].pos = position
                        position = position + 1
                    else:
                        users[i].pos = position
            up_to_classification = datetime.datetime.today().strftime('%Y-%m-%d')
            from_classification = firstDayOfCourse()

            return render(request, 'results.html', {'collection': collection, 'groups': groups_user,
                                                    'users': users, 'login': request.user,
                                                    'group0': group0,
                                                    'to_fixed': up_to_classification,
                                                    'from_date': from_classification_date,
                                                    'to_date': up_to_classification_date,
                                                    'from_fixed': from_classification,
                                                    'end_date': end, 'start_date': start})

        return HttpResponseForbidden("Forbidden")
    except ValueError:
        return HttpResponseNotFound("El identificador de grupo no tiene el formato correcto")


@login_required
def show_results(request):
    """shows the links to enter the results of each collection"""
    if not Group.objects.all():
        # Show an informative message if there are not groups in the system
        return render(request, 'generic_error_message.html',
                      {'error': ['¡Lo sentimos! No se han configurado grupos configurados en el juez para ver '
                                 'resultados']})

    cols = Collection.objects.all().order_by('position', '-creation_date')
    groups_user = request.user.groups.all().order_by('name')
    if groups_user.count() == 0 and not request.user.is_staff:
        return render(request, 'generic_error_message.html',
                      {'error': ['¡Lo sentimos! No tienes asignado un grupo de la asignatura.',
                                 'Por favor, contacta con tu profesor para te asignen un grupo de clase.']
                       })
    if groups_user.count() == 0 and request.user.is_staff:
        groups_user = Group.objects.all().order_by('name')
    for results in cols:
        # Templates can only invoke nullary functions or access object attribute, so we store
        # the number of problems solved by the user in an attribute
        results.num_solved = results.num_solved_by_user(request.user)
    up_to_classification = datetime.datetime.today().strftime('%Y-%m-%d')
    up_to_classification_date = datetime.datetime.strptime(up_to_classification, '%Y-%m-%d')

    from_classification = firstDayOfCourse()
    from_classification_date = datetime.datetime.strptime(from_classification, '%Y-%m-%d')
    return render(request, 'result.html', {'user': request.user, 'results': cols, 'group': groups_user[0].id,
                                           'start_date': from_classification, 'from_fixed': from_classification,
                                           'from_date': from_classification_date,
                                           'to_date': up_to_classification_date,
                                           'to_fixed': up_to_classification,
                                           'end_date': up_to_classification})


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
    problem = get_child_problem(problem_id)
    # Stores the flag in an attribute so that the template can use it
    problem.solved = problem.solved_by_user(request.user)
    return render(request, problem.template(), {'problem': problem})


@login_required
def show_submissions(request):
    """Shows all the submissions of the current user"""

    try:
        pk_problem = request.GET.get('problem_id')
        id_user = request.GET.get('user_id')
        if pk_problem is not None or id_user is not None:
            if int(id_user) == request.user.id and not request.user.is_staff:
                start = request.GET.get('start')
                end = request.GET.get('end')
                if start is not None or end is not None:
                    return HttpResponseForbidden("Forbidden")
                problem = get_object_or_404(Problem, pk=pk_problem)
                subs = Submission.objects.filter(user=request.user).filter(problem=problem.id).order_by('-pk')
            elif request.user.is_staff:
                start = request.GET.get('start')
                end = request.GET.get('end')
                problem = get_object_or_404(Problem, pk=pk_problem)
                user = get_user_model().objects.filter(id=id_user)
                subs = Submission.objects.filter(user=user.get())\
                    .filter(problem=problem.id, creation_date__range=[start, end]).order_by('-pk')
            else:
                return HttpResponseForbidden("Forbidden")

        else:
            subs = Submission.objects.filter(user=request.user).order_by('-pk')
        for submission in subs:
            submission.veredict_pretty = VeredictCode(submission.veredict_code).html_short_name()
        return render(request, 'submissions.html', {'submissions': subs})
    except ValueError:
        return HttpResponseNotFound("El identificador no tiene el formato correcto")


@login_required
def show_submission(request, submission_id):
    """Shows a submission of the current user"""
    submission = get_object_or_404(Submission, pk=submission_id)
    if submission.user != request.user and not request.user.is_staff:
        return HttpResponseForbidden("Forbidden")
    submission.veredict_pretty = VeredictCode(submission.veredict_code).html_short_name()
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
    problem = get_child_problem(problem_id)
    response = HttpResponse()
    response['Content-Type'] = 'application/sql'
    response['Content-Disposition'] = "attachment; filename=create_insert.sql"
    response.write(problem.create_sql + '\n\n' + problem.insert_sql)
    return response


@login_required
# pylint does not understand the dynamic attributes in VeredictCode (TextChoices), so we need to disable
# no-member warning in this specific function
# pylint: disable=no-member
def submit(request, problem_id):
    """Process a user submission"""
    # Error 404 if there is no Problem 'pk'
    general_problem = get_object_or_404(Problem, pk=problem_id)
    problem = get_child_problem(problem_id)
    submit_form = SubmitForm(request.POST)
    data = {'veredict': VeredictCode.IE, 'title': VeredictCode.IE.label,
            'message': VeredictCode.IE.message(), 'feedback': ''}
    code = ''
    if submit_form.is_valid():
        try:
            # AC or WA
            code = submit_form.cleaned_data['code']
            data['veredict'], data['feedback'] = problem.judge(code, OracleExecutor.get())
            data['title'] = data['veredict'].label
            data['message'] = data['veredict'].message()
        except ExecutorException as excp:
            # Exceptions when judging: RE, TLE, VE or IE
            if excp.error_code == OracleStatusCode.EXECUTE_USER_CODE:
                data = {
                    'veredict': VeredictCode.RE,
                    'title': VeredictCode.RE.label,
                    'message': VeredictCode.RE.message(),
                    'feedback': f'{excp.statement} --> {excp.message}' if problem.problem_type() == ProblemType.FUNCTION
                    else excp.message,
                    'position': excp.position
                }
            elif excp.error_code == OracleStatusCode.TLE_USER_CODE:
                data = {'veredict': VeredictCode.TLE, 'title': VeredictCode.TLE.label,
                        'message': VeredictCode.TLE.message(), 'feedback': ''}
            elif excp.error_code == OracleStatusCode.NUMBER_STATEMENTS:
                data = {'veredict': VeredictCode.VE, 'title': VeredictCode.VE.label,
                        'message': VeredictCode.VE.message(problem), 'feedback': excp.message}
            elif excp.error_code == OracleStatusCode.COMPILATION_ERROR:
                data = {'veredict': VeredictCode.WA, 'title': VeredictCode.WA.label,
                        'message': VeredictCode.WA.message(), 'feedback': compile_error_to_html_table(excp.message)}
    else:
        data = {'veredict': VeredictCode.VE, 'title': VeredictCode.VE.label,
                'message': VeredictCode.VE.message(), 'feedback': ''}

    submission = Submission(code=code, veredict_code=data['veredict'], veredict_message=data['message'],
                            user=request.user, problem=general_problem)
    submission.save()
    logger.debug('Stored submission %s', submission)
    return JsonResponse(data)


@login_required
def password_change_done(request):
    """Password change confirmation"""
    return render(request, 'password_change_done.html')
