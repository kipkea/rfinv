from django.shortcuts import render
from django.http import HttpResponse
from django.utils import timezone
from django.template.loader import render_to_string
from weasyprint import HTML

from .models import Inventory, Location, Inspection

def report_dashboard(request):
    """ แสดงหน้าจอสำหรับเลือกเงื่อนไขเพื่อพิมพ์รายงาน """
    locations = Location.objects.all().order_by('name')
    products = Inventory.objects.all().order_by('name')
    return render(request, 'reports.html', {
        'locations': locations,
        'products': products,
    })

def generate_location_report(request):
    """ สร้างและคืนค่ารายงาน PDF: สินค้าตามตำแหน่ง """
    location_id = request.GET.get('location_id')
    
    if location_id == 'ALL':
        locations = Location.objects.all().order_by('name')
    else:
        locations = Location.objects.filter(id=location_id)
        
    for loc in locations:
        loc.items = loc.current_items.all().order_by('name')
        
    context = {
        'request': request, # จำเป็นต้องส่ง request เพื่อใช้ดึง Absolute Path ของรูปภาพ
        'system_name': 'ระบบจัดการคลังสินค้า (RFInv)',
        'report_name': 'รายงานสินค้าแบ่งตามตำแหน่ง',
        'printed_by': request.user.get_full_name() or request.user.username,
        'printed_time': timezone.now(),
        'locations': locations,
    }
    
    html_string = render_to_string('location_report.html', context)
    pdf = HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="location_report.pdf"'
    return response

def generate_product_report(request):
    """ สร้างและคืนค่ารายงาน PDF: ประวัติการตรวจสอบสินค้า """
    product_id = request.GET.get('product_id')
    
    if product_id == 'ALL':
        products = Inventory.objects.all().order_by('name')
    else:
        products = Inventory.objects.filter(id=product_id)
        
    for prod in products:
        prod.history_records = prod.inspections.all().order_by('-inspected_at')
        
    context = {
        'request': request,
        'system_name': 'ระบบจัดการคลังสินค้า (RFInv)',
        'report_name': 'รายงานประวัติการตรวจสอบและพิกัดสินค้า',
        'printed_by': request.user.get_full_name() or request.user.username,
        'printed_time': timezone.now(),
        'products': products,
    }
    
    html_string = render_to_string('product_report.html', context)
    pdf = HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="product_report.pdf"'
    return response