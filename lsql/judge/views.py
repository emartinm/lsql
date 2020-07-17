import logging

from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

from .exceptions import ExecutorException
from .forms import SubmitForm
from .models import Collection, Problem, SelectProblem, DMLProblem, ProcProblem, FunctionProblem, TriggerProblem
from .oracleDriver import OracleExecutor
from .types import VeredictCode, OracleStatusCode

logger = logging.getLogger(__name__)


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
        e.num_solved = e.num_solved_by_user(request.user)
    return render(request, 'collections.html', {'collections': cols})


@login_required
def collection(request, pk):
    c = get_object_or_404(Collection, pk=pk)
    return render(request, 'collection.html', {'collection': c})


@login_required
def problem(request, pk):
    # Error 404 if there is no a Problem pk
    get_object_or_404(Problem, pk=pk)
    # Look for problem pk in all the Problem classes
    p = get_child_problem(pk)
    return render(request, p.template(), {'problem': p})


@login_required
def submit(request, pk):
    # Error 404 if there is no Problem 'pk'
    get_object_or_404(Problem, pk=pk)
    p = get_child_problem(pk)
    submit_form = SubmitForm(request.POST)
    data = {'veredict': None, 'title': '', 'message': '', 'feedback': ''}
    if submit_form.is_valid():
        try:
            # AC or WA
            data['veredict'], data['feedback'] = p.judge(submit_form.cleaned_data['code'], OracleExecutor.get())
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
    return JsonResponse(data)


@login_required
def password_change_done(request):
    return render(request, 'password_change_done.html')
