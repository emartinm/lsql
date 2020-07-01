import logging

from django.http import HttpResponseRedirect, HttpResponse, HttpResponseBadRequest, JsonResponse
from django.urls import reverse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

from .exceptions import ExecutorException
from .forms import SubmitForm
from .models import Collection, Problem, SelectProblem, DMLProblem, ProcProblem, FunctionProblem, TriggerProblem, \
    Submission
from .oracleDriver import OracleExecutor

logger = logging.getLogger(__name__)


def get_child_problem(pk):
    """Look for problem 'pk' in the different child classes of Problem"""
    classes = [SelectProblem, DMLProblem, FunctionProblem, ProcProblem, TriggerProblem]
    i = 0
    p = None
    while i < len(classes) and p is None:
        q = classes[i].objects.filter(pk=pk)
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
        executor = OracleExecutor.get()
        try:
            data['veredict'], data['feedback'] = p.judge(submit_form.code, executor)  # FIXME
            data['title'] = titles_from_veredict[data['veredict']]  # FIXME: crear mapas
            data['message'] = messages_from_veredict[data['veredict']]
        except ExecutorException as e:
            pass  # TODO
    else:
        data['veredict'] = Submission.VeredictCode.VE
        data['title'] = 'Error de validación'
        data['message'] = 'Los datos enviados no son correctos.'
    return JsonResponse(data)


@login_required
def password_change_done(request):
    return render(request, 'password_change_done.html')
