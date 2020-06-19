import logging

from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout

from .forms import LoginForm
from .models import Collection

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
    c = Collection.objects.filter(pk=pk)
    return render(request, 'collection.html', {'collection': c})


@login_required
def user(request, pk):
    return HttpResponse(f'hola guapo {pk}')


def login_view(request):
    if request.method == 'GET':
        login_form = LoginForm()
        return render(request, 'login.html', {'form': login_form})
    elif request.method == 'POST':
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            u = authenticate(request,
                             username=login_form.cleaned_data['username'],
                             password=login_form.cleaned_data['password'])
            if u is not None:
                logout(request)
                login(request, u)
                # Redirect to a success page.
                # TODO: redirect to the route in parameter next: ?next=/sql/collection
                return HttpResponseRedirect(reverse('judge:collections'))
            else:
                # Return an 'invalid login' error message.
                # TODO
                pass


@login_required
def logout_view(request):
    request.session.flush()
    return render(request, 'logout.html')
