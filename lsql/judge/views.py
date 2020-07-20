from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from logzero import logger

from .exceptions import ExecutorException
from .forms import SubmitForm
from .models import Collection, Problem, SelectProblem, DMLProblem, ProcProblem, FunctionProblem, TriggerProblem, \
    Submission
from .oracleDriver import OracleExecutor
from .types import VeredictCode, OracleStatusCode


def get_child_problem(pk):
    """Look for problem 'pk' in the different child classes of Problem"""
    classes = [SelectProblem, DMLProblem, FunctionProblem, ProcProblem, TriggerProblem]
    i = 0
    p = None
    while i < len(classes) and p is None:
        q = classes[i].objects.filter(pk=pk)
        i += 1
        if q:
            p = q[0]
    return p


def index(_):
    return HttpResponseRedirect(reverse('judge:collections'))


@login_required
def collections(request):
    cols = Collection.objects.all().order_by('-creation_date')
    for e in cols:
        # Templates can only invoke nullary functions or access object attribute, so we store
        # the number of problems solved by the user in an attribute
        e.num_solved = e.num_solved_by_user(request.user)
    return render(request, 'collections.html', {'collections': cols})


@login_required
def collection(request, pk):
    c = get_object_or_404(Collection, pk=pk)
    # New attribute to store the list of problems and include the number of submission in each problem
    c.problem_list = c.problems()
    for p in c.problem_list:
        p.num_submissions = p.num_submissions_by_user(request.user)
        p.solved = p.solved_by_user(request.user)
    return render(request, 'collection.html', {'collection': c})


@login_required
def problem(request, pk):
    # Error 404 if there is no a Problem pk
    get_object_or_404(Problem, pk=pk)
    # Look for problem pk in all the Problem classes
    p = get_child_problem(pk)
    p.solved = p.solved_by_user(request.user)  # Stores the flag in an attribute so that the template can use it
    return render(request, p.template(), {'problem': p})


@login_required
def submissions(request):
    subs = Submission.objects.filter(user=request.user)
    for s in subs:
        s.veredict_pretty = VeredictCode(s.veredict_code).html_short_name()
    return render(request, 'submissions.html', {'submissions': subs})


@login_required
def submission(request, pk):
    s = get_object_or_404(Submission, pk=pk)
    s.veredict_pretty = VeredictCode(s.veredict_code).html_short_name()
    return render(request, 'submission.html', {'submission': s})


@login_required
def submit(request, pk):
    # Error 404 if there is no Problem 'pk'
    general_problem = get_object_or_404(Problem, pk=pk)
    p = get_child_problem(pk)
    submit_form = SubmitForm(request.POST)
    data = {'veredict': None, 'title': '', 'message': '', 'feedback': ''}
    code = ''
    if submit_form.is_valid():
        try:
            # AC or WA
            code = submit_form.cleaned_data['code']
            data['veredict'], data['feedback'] = p.judge(code, OracleExecutor.get())
            data['title'] = data['veredict'].label
            data['message'] = data['veredict'].message()
        except ExecutorException as e:
            # Exceptions when judging: RE, TLE, VE or IE
            if e.error_code == OracleStatusCode.EXECUTE_USER_CODE:
                data = {'veredict': VeredictCode.RE, 'title': VeredictCode.RE.label,
                        'message': VeredictCode.RE.message(), 'feedback': e.message}
            elif e.error_code == OracleStatusCode.TLE_USER_CODE:
                data = {'veredict': VeredictCode.TLE, 'title': VeredictCode.TLE.label,
                        'message': VeredictCode.TLE.message(), 'feedback': ''}
            elif e.error_code == OracleStatusCode.NUMBER_STATEMENTS:
                data = {'veredict': VeredictCode.VE, 'title': VeredictCode.VE.label,
                        'message': VeredictCode.VE.message(), 'feedback': e.message}
            else:
                data = {'veredict': VeredictCode.IE, 'title': VeredictCode.IE.label,
                        'message': VeredictCode.IE.message(), 'feedback': ''}
    else:
        data = {'veredict': VeredictCode.VE, 'title': VeredictCode.VE.label,
                'message': VeredictCode.VE.message(), 'feedback': ''}

    s = Submission(code=code, veredict_code=data['veredict'], veredict_message=data['message'],
                   user=request.user, problem=general_problem)
    s.save()
    logger.debug(f'Stored submission {s}')
    return JsonResponse(data)


@login_required
def password_change_done(request):
    return render(request, 'password_change_done.html')
