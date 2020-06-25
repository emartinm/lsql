import logging

from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

from .models import Collection, Problem, SelectProblem, DMLProblem, ProcProblem, FunctionProblem, TriggerProblem

logger = logging.getLogger(__name__)


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
    classes = [SelectProblem, DMLProblem, FunctionProblem, ProcProblem, TriggerProblem]
    i = 0
    p = None
    while i < len(classes) and p is None:
        q = classes[i].objects.filter(pk=pk)
        if q:
            p = q[0]
    return render(request, p.template(), {'problem': p})


@login_required
def password_change_done(request):
    return render(request, 'password_change_done.html')
