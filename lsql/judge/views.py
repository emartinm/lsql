# -*- coding: utf-8 -*-
"""
Copyright Enrique Martín <emartinm@ucm.es> 2020

Functions that process HTTP connections
"""

from django.http import HttpResponseRedirect, JsonResponse, HttpResponseForbidden
from django.http.response import HttpResponse, HttpResponseNotFound
from django.urls import reverse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from logzero import logger
from .exceptions import ExecutorException
from .feedback import compile_error_to_html_table
from .forms import SubmitForm
from .models import Collection, Problem, SelectProblem, DMLProblem, ProcProblem, FunctionProblem, TriggerProblem, \
    Submission
from .oracle_driver import OracleExecutor
from .types import VeredictCode, OracleStatusCode, ProblemType
from django.contrib.auth.models import User, Group


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
    """compare exercises for positions"""
    if user_1.resolved == user_2.resolved and user_1.score == user_2.score:
        return False
    else:
        return True


def index(_):
    """Redirect root access to collections"""
    return HttpResponseRedirect(reverse('judge:collections'))


@login_required()
def show_result(request, collection_id):
    """show datatable of a collection"""
    """Shows a collection"""
    position = 1
    try:
        groups_user = request.user.groups.all().order_by('name')
        group_id = request.GET.get('group')
        if group_id is None:
            group_id = groups_user[0].id
        collection = get_object_or_404(Collection, pk=collection_id)
        group0 = get_object_or_404(Group, pk=group_id)
        users = User.objects.filter(groups__name=group0.name)
        if users.filter(id=request.user.id):
            group0.name = group0.name
            group0.id = group_id
            groups_user = groups_user.exclude(id=group_id)
            collection.problem_list = collection.problems()
            collection.total_problem = collection.problem_list.count()
            users = users.exclude(is_staff=True)
            for i in users:
                i.collection = []
                i.resolved = 0
                i.score = 0
                for z in range(0, collection.problem_list.count()):
                    ex = 0
                    intents = 0
                    p = collection.problem_list[z]
                    i.first_AC = 0
                    subs = Submission.objects.filter(user=i).filter(problem=p.id).order_by('pk')
                    for submission in range(0, len(subs)):
                        if VeredictCode(subs[submission].veredict_code) == 'AC':
                            ex = ex + 1
                            if ex == 1:
                                i.first_AC = submission + 1
                                i.score = i.score + submission + 1
                        intents = intents + 1

                    if intents > 0 and i.first_AC == 0:
                        p.num_submissions = f"{ex}/{intents} ({intents})"
                    else:
                        p.num_submissions = f"{ex}/{intents} ({i.first_AC})"  # collection.problem_list[z].num_submissions_by_user(i)
                    p.solved = collection.problem_list[z].solved_by_user(i)
                    #i.intents = i.intents + collection.problem_list[z].num_submissions_by_user(i)
                    if p.solved:
                        i.resolved = i.resolved + 1
                    i.collection.append(p)

            users = sorted(users, key=lambda x: (x.resolved, -x.score), reverse=True)

            for i in range(0, len(users)):
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

            return render(request, 'results.html', {'collection': collection, 'groups': groups_user, 'users': users,
                                                    'login': request.user, 'group0': group0})
        else:
            return HttpResponseForbidden("Forbidden")
    except ValueError as ex:
        return HttpResponseNotFound("El identificador de grupo no tiene el formato correcto")


@login_required
def show_results(request):
    """show all collections"""
    cols = Collection.objects.all().order_by('position', '-creation_date')
    groups_user = request.user.groups.all().order_by('name')
    if groups_user.count() == 0:
        return HttpResponseForbidden("Vacio, aquí crear un mensaje")
    else:
        for results in cols:
            # Templates can only invoke nullary functions or access object attribute, so we store
            # the number of problems solved by the user in an attribute
            results.num_solved = results.num_solved_by_user(request.user)
        return render(request, 'result.html', {'results': cols, 'group': groups_user[0].id})


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
        if pk_problem is not None:
            problem = get_object_or_404(Problem, pk=pk_problem)
            subs = Submission.objects.filter(user=request.user).filter(problem=problem.id).order_by('-pk')

        else:
            subs = Submission.objects.filter(user=request.user).order_by('-pk')
        for submission in subs:
            submission.veredict_pretty = VeredictCode(submission.veredict_code).html_short_name()
        return render(request, 'submissions.html', {'submissions': subs})
    except ValueError as ex:
        return HttpResponseNotFound("EL identificador no tiene el formato correcto")


"""mirar esto es para mis envios que sea el de uno en concreto"""
"""@login_required
def show_submissions(request):
   
    problema = get_child_problem(10)
    subs = Submission.objects.filter(user=request.user).filter(problem=problema).order_by('-pk')
    for submission in subs:
        submission.veredict_pretty = VeredictCode(submission.veredict_code).html_short_name()
    return render(request, 'submissions.html', {'submissions': subs})"""


@login_required
def show_submission(request, submission_id):
    """Shows a submission of the current user"""
    submission = get_object_or_404(Submission, pk=submission_id)
    if submission.user != request.user:
        return HttpResponseForbidden("Forbidden")
    submission.veredict_pretty = VeredictCode(submission.veredict_code).html_short_name()
    return render(request, 'submission.html', {'submission': submission})


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
                    'veredict': VeredictCode.RE, 'title': VeredictCode.RE.label,
                    'message': VeredictCode.RE.message(),
                    'feedback': f'{excp.statement} --> {excp.message}' if problem.problem_type() == ProblemType.FUNCTION
                    else excp.message}
            elif excp.error_code == OracleStatusCode.TLE_USER_CODE:
                data = {'veredict': VeredictCode.TLE, 'title': VeredictCode.TLE.label,
                        'message': VeredictCode.TLE.message(), 'feedback': ''}
            elif excp.error_code == OracleStatusCode.NUMBER_STATEMENTS:
                data = {'veredict': VeredictCode.VE, 'title': VeredictCode.VE.label,
                        'message': VeredictCode.VE.message(), 'feedback': excp.message}
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
