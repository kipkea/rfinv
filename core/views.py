from django.shortcuts import render

# Create your views here.


from django.views.generic import ListView
from .models import Person

class PersonListView(ListView):
    model = Person
    template_name = 'core/people.html'