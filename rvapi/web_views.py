from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Inventory, Location

def web_login(request):
    error_msg = None
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            login(request, user)
            return redirect('web_dashboard')
        else:
            error_msg = "Username หรือ Password ไม่ถูกต้อง"
            
    return render(request, 'rvapi/login.html', {'error': error_msg})

def web_logout(request):
    logout(request)
    return redirect('web_login')

@login_required(login_url='web_login')
def dashboard(request):
    # ดึงข้อมูลจาก Model โดยตรง
    inv_count = Inventory.objects.count()
    loc_count = Location.objects.count()
    
    return render(request, 'rvapi/dashboard.html', {
        'inv_count': inv_count,
        'loc_count': loc_count,
    })

@login_required(login_url='web_login')
def inventory_list(request):
    items = Inventory.objects.select_related('rfid_tag', 'current_location').all()
    return render(request, 'rvapi/inventory.html', {'items': items})