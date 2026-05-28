from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import OuterRef, Subquery
from .models import Inventory, Location, RFIDTag

@login_required(login_url='web_login')
def inventory_list(request):
    # 1. ตรวจสอบว่ามีการส่งข้อมูลจากฟอร์ม Modal มาหรือไม่
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'edit':
            # --- กรณีแก้ไขข้อมูลสินค้า ---
            item_id = request.POST.get('item_id')
            item = get_object_or_404(Inventory, id=item_id)
            item.name = request.POST.get('name')
            
            # อัปเดตรูปภาพใหม่ถ้ามีการอัปโหลดมา (ถ้าไม่อัปโหลดมาจะใช้รูปเดิม)
            image = request.FILES.get('image')
            if image:
                item.image = image
                
            item.save()
            
        elif action == 'delete':
            # --- กรณีลบข้อมูลสินค้า ---
            item_id = request.POST.get('item_id')
            item = get_object_or_404(Inventory, id=item_id)
            item.delete()
            
        else:
            # --- กรณีเพิ่มข้อมูลใหม่ (สินค้า หรือ สถานที่เก็บ) ---
            item_type = request.POST.get('item_type', 'inventory')
            name = request.POST.get('name')
            rfid_code = request.POST.get('rfid_tag')

            tag_obj = None
            if rfid_code:
                tag_obj, created = RFIDTag.objects.get_or_create(rfid_code=rfid_code)

            if item_type == 'location':
                new_location = Location(
                    name=name,
                    rfid_tag=tag_obj
                )
                if request.user.is_authenticated:
                    new_location.created_by = request.user
                new_location.save()
            else:
                image = request.FILES.get('image')
                new_inventory = Inventory(
                    name=name,
                    image=image,
                    rfid_tag=tag_obj
                )
                
                if request.user.is_authenticated:
                    new_inventory.registered_by = request.user
                    
                new_inventory.save()

        # 4. รีเฟรชหน้าเว็บกลับมาที่เดิมเพื่ออัปเดตตาราง และป้องกันการกด F5 แล้วส่งฟอร์มซ้ำ
        # หมายเหตุ: หากขึ้น Error ตรงนี้ ให้เปลี่ยน 'web_inventory' เป็นชื่อที่ตั้งไว้ใน path ของ urls.py
        return redirect('web_inventory')

    # --- ส่วนการทำงานปกติเมื่อโหลดหน้าเว็บ (GET Request) ---
    sort_by = request.GET.get('sort', 'id')  # ค่าเริ่มต้นให้เรียงตาม id
    sort_dir = request.GET.get('dir', 'desc') # ค่าเริ่มต้นให้เรียงจากมากไปน้อย
    location_filter = request.GET.get('location') # ตัวแปรรับค่าค้นหาสถานที่
    
    # จับคู่พารามิเตอร์กับฟิลด์ใน Database
    valid_sort_fields = {
        'id': 'id',
        'name': 'name',
        'rfid': 'rfid_tag__rfid_code',
        'location': 'current_location__name'
    }
    db_sort_field = valid_sort_fields.get(sort_by, 'id')
    if sort_dir == 'desc':
        db_sort_field = f'-{db_sort_field}'

    items = Inventory.objects.select_related('rfid_tag', 'current_location').all()
    
    # ตรวจสอบและกรองข้อมูลตามสถานที่
    if location_filter:
        if location_filter == 'none':
            items = items.filter(current_location__isnull=True)
        else:
            items = items.filter(current_location__name=location_filter)
            
    items = items.order_by(db_sort_field)
    
    # --- ส่วนการแบ่งหน้า (Pagination) ---
    paginator = Paginator(items, 100)  # แสดงผล 10 รายการต่อ 1 หน้า
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # ดึง RFID Code ที่เป็นของแท็กทั่วไป (is_location=False) และยังไม่ถูกผูกกับสินค้าใด (inventory_profile__isnull=True)
    available_rfid_tags = RFIDTag.objects.filter(
        is_location=False, 
        inventory_profile__isnull=True
    ).order_by('-registered_at') # เรียงเอาแท็กใหม่ล่าสุดขึ้นก่อน
    
    # ส่งตัวแปร page_obj และ available_rfid_tags ไปให้ inventory.html
    return render(request, 'inventory.html', {
        'page_obj': page_obj, 
        'available_rfid_tags': available_rfid_tags,
        'current_sort': sort_by,
        'current_dir': sort_dir,
        'current_location': location_filter
    })

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
            
    return render(request, 'login.html', {'error': error_msg})

def web_logout(request):
    logout(request)
    return redirect('web_login')

@login_required(login_url='web_login')
def dashboard(request):
    # ดึงข้อมูลจาก Model โดยตรง
    inv_count = Inventory.objects.count()
    loc_count = Location.objects.count()
    
    # 1. จำนวนรหัสที่ยังไม่ได้กำหนดข้อมูล (ไม่มีทั้งใน Inventory และ Location)
    unassigned_rfid_count = RFIDTag.objects.filter(
        location_profile__isnull=True,
        inventory_profile__isnull=True
    ).count()

    # 2. ค้นหาคนตรวจสอบล่าสุด (จากประวัติ Inspection)
    from .models import Inspection
    latest_inspection = Inspection.objects.filter(
        found_inventories=OuterRef('pk')
    ).order_by('-inspected_at')

    inventories = Inventory.objects.select_related('current_location').annotate(
        inspected_by_name=Subquery(latest_inspection.values('inspected_by__username')[:1])
    ).order_by('current_location__name', 'name')

    # 3. จัดกลุ่มสินค้าตามสถานที่เก็บ
    grouped_items = {}
    no_location_items = []

    for item in inventories:
        if item.current_location:
            loc_name = item.current_location.name
            if loc_name not in grouped_items:
                grouped_items[loc_name] = []
            grouped_items[loc_name].append(item)
        else:
            no_location_items.append(item)

    return render(request, 'dashboard.html', {
        'inv_count': inv_count,
        'loc_count': loc_count,
        'unassigned_rfid_count': unassigned_rfid_count,
        'grouped_items': grouped_items,
        'no_location_items': no_location_items,
    })
