from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic

from .models import Collection


def index(request):
    return HttpResponseRedirect(reverse('judge:collections'))


class AllCollectionsView(generic.ListView):
    template_name = 'collections.html'
    # context_object_name = 'latest_question_list'

    def get_queryset(self):
        """
        Return all the collections
        """
        return Collection.objects.all()


class CollectionView(generic.DetailView):
    model = Collection
    template_name = 'collection.html'
