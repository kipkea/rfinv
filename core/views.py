from django.shortcuts import render

# Create your views here.


from django.views.generic import ListView
from .models import Person
from .tables import PersonTable

class PersonListView(ListView):
    model = Person
    table_class = PersonTable
    template_name = 'core/people.html'