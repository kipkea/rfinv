from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.

def Home(request):
    #return HttpResponse('<h1>Hello World</h1>')
    temp = 50.02
    context = {'temp':temp}
    return render(request, 'monitor/home.html',context)
