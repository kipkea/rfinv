import os
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Q

# ReportLab imports
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from .models import Inventory, Location, Inspection


# คลาส Canvas สำหรับทำเลขหน้าแบบ หน้าปัจจุบัน/หน้าทั้งหมด และลายน้ำ
class PageNumCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self.pages = []
        self.draw_watermark()

    def showPage(self):
        # เก็บสถานะของแต่ละหน้าไว้ก่อนจะขึ้นหน้าใหม่
        self.pages.append(dict(self.__dict__))
        self._startPage()
        self.draw_watermark()

    def save(self):
        # วาดเลขหน้าลงทุกหน้าก่อนจะเซฟไฟล์
        page_count = len(self.pages)
        for page in self.pages:
            self.__dict__.update(page)
            self.draw_page_number(page_count)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_watermark(self):
        self.saveState()
        watermark_path = os.path.join(settings.BASE_DIR, 'assets', 'watermark0.png')
        if os.path.exists(watermark_path):
            img_width = 12 * cm
            img_height = 12 * cm
            x = (A4[0] - img_width) / 2
            y = (A4[1] - img_height) / 2
            self.drawImage(watermark_path, x, y, width=img_width, height=img_height, mask='auto')
        self.restoreState()

    def draw_page_number(self, page_count):
        self.saveState()

        page_num = self._pageNumber
        text = f"หน้า {page_num}/{page_count}"
        try:
            self.setFont('THSarabun', 11)
        except Exception:
            self.setFont('Helvetica', 11)
        self.drawRightString(A4[0] - 1.5*cm, 1.5*cm, text)
        
        self.restoreState()

# ฟังก์ชันสำหรับลงทะเบียนฟอนต์ภาษาไทยเพื่อใช้งานใน ReportLab
def register_thai_font():
    font_name, font_bold = 'Helvetica', 'Helvetica-Bold'
    
    # 1. หารายการโฟลเดอร์ทั้งหมดที่เป็นไปได้สำหรับเก็บไฟล์ Static
    font_dirs = []
    if getattr(settings, 'STATIC_ROOT', None):
        font_dirs.append(os.path.join(str(settings.STATIC_ROOT), 'fonts')) # AWS / Production
    for static_dir in getattr(settings, 'STATICFILES_DIRS', []):
        font_dirs.append(os.path.join(str(static_dir), 'fonts')) # Local Dev
    
    font_dirs.append(os.path.join(str(settings.BASE_DIR), 'assets', 'fonts')) # Fallback

    font_path = None
    bold_path = None

    # 2. วนลูปหาไฟล์ฟอนต์จาก Path ทั้งหมดที่มี (ครอบคลุมทั้ง Dev และ AWS)
    for base_dir in font_dirs:
        test_font_path = os.path.join(base_dir, 'THSarabunNew.ttf')
        if os.path.exists(test_font_path):
            font_path = test_font_path
            bold_path = os.path.join(base_dir, 'THSarabunNew Bold.ttf')
            if not os.path.exists(bold_path):
                bold_path = os.path.join(base_dir, 'THSarabunNew-Bold.ttf')
            break

    try:
        if font_path and os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('THSarabun', font_path))
            font_name = 'THSarabun'
        if bold_path and os.path.exists(bold_path):
            pdfmetrics.registerFont(TTFont('THSarabun-Bold', bold_path))
            font_bold = 'THSarabun-Bold'
            
        # ผูกฟอนต์เข้าด้วยกันเพื่อให้แท็ก <b> และ <i> ใช้งานได้ใน Paragraph
        if font_name == 'THSarabun' and font_bold == 'THSarabun-Bold':
            registerFontFamily('THSarabun', normal='THSarabun', bold='THSarabun-Bold', italic='THSarabun', boldItalic='THSarabun-Bold')
        else:
            print("⚠️ คำเตือน: ไม่พบไฟล์ฟอนต์ภาษาไทย โปรดตรวจสอบโฟลเดอร์ fonts ใน assets หรือ STATIC_ROOT")
    except Exception as e:
        print("Font error:", e)
    return font_name, font_bold

def report_dashboard(request):
    """ แสดงหน้าจอสำหรับเลือกเงื่อนไขเพื่อพิมพ์รายงาน """
    locations = Location.objects.all().order_by('name')
    products = Inventory.objects.all().order_by('name')
    return render(request, 'reports.html', {
        'locations': locations,
        'products': products,
    })

def generate_location_report(request):
    """ สร้างและคืนค่ารายงาน PDF: สินค้าตามตำแหน่ง (ใช้ ReportLab) """
    location_id = request.GET.get('location_id')
    
    if location_id == 'ALL':
        locations = Location.objects.all().order_by('name')
    else:
        locations = Location.objects.filter(id=location_id)
        
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="location_report.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=A4, rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm,
                            title="รายงานสินค้าแบ่งตามตำแหน่ง", author="ระบบจัดการคลังสินค้า (RFInv)")
    font_name, font_bold = register_thai_font()
    styles = getSampleStyleSheet()
    
    style_normal = ParagraphStyle('Normal_Thai', parent=styles['Normal'], fontName=font_name, fontSize=13, wordWrap='CJK')
    style_h2 = ParagraphStyle('H2_Thai', parent=styles['Heading2'], fontName=font_bold, fontSize=18, alignment=1, wordWrap='CJK')
    style_h3 = ParagraphStyle('H3_Thai', parent=styles['Heading3'], fontName=font_bold, fontSize=16, alignment=1, wordWrap='CJK')
    style_h4 = ParagraphStyle('H4_Thai', parent=styles['Heading4'], fontName=font_bold, fontSize=14, textColor=colors.HexColor('#0d6efd'), wordWrap='CJK')

    elements = []
    elements.append(Paragraph('ระบบจัดการคลังสินค้า (RFInv)', style_h2))
    elements.append(Paragraph('รายงานสินค้าแบ่งตามตำแหน่ง', style_h3))
    
    printed_by = request.user.get_full_name() or request.user.username
    printed_time = timezone.localtime(timezone.now()).strftime("%d/%m/%Y %H:%M")
    
    meta_info = f"<b>ผู้พิมพ์:</b> {printed_by} &nbsp;&nbsp;&nbsp;&nbsp; <b>เวลาพิมพ์:</b> {printed_time}"
    elements.append(Paragraph(meta_info, style_normal))
    elements.append(Spacer(1, 10))
    
    for loc in locations:
        elements.append(Paragraph(f"ตำแหน่ง: {loc.name}", style_h4))
        elements.append(Spacer(1, 5))
        
        data = [['รูปภาพ', 'ชื่อสินค้า', 'RFID Code']]
        # กรองเอาเฉพาะสินค้าที่สถานะปกติ (ACTIVE)
        items = loc.current_items.filter(status='ACTIVE').order_by('name')
        if not items:
            data.append(['', 'ไม่พบรายการสินค้าในตำแหน่งนี้', ''])
        
        for item in items:
            img = Paragraph('<font color="#999999">ไม่มีรูป</font>', style_normal)
            if item.image and item.image.name:
                img_path = os.path.join(settings.MEDIA_ROOT, item.image.name)
                if os.path.exists(img_path):
                    img = Image(img_path, width=50, height=50)
            
            rfid = item.rfid_tag.rfid_code if item.rfid_tag else "ไม่มี RFID"
            data.append([img, Paragraph(item.name, style_normal), Paragraph(rfid, style_normal)])
            
        t = Table(data, colWidths=[2.5*cm, 8.5*cm, 5*cm])
        table_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f1f1')),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
            ('FONTNAME', (0, 0), (-1, 0), font_bold),
            ('FONTNAME', (0, 1), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]
        if not items:
            table_style.extend([('SPAN', (1, 1), (2, 1)), ('ALIGN', (1,1), (1,1), 'CENTER')])
            
        t.setStyle(TableStyle(table_style))
        elements.append(t)
        elements.append(Spacer(1, 20))
        
    doc.build(elements, canvasmaker=PageNumCanvas)
    return response

def generate_inspection_pdf(request, pk):
    """ สร้างรายงานสรุปผลการตรวจสอบรายครั้ง """
    inspection = get_object_or_404(Inspection, pk=pk)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="inspection_{pk}.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=A4, rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm,
                            title=f"รายงานสรุปผลการตรวจสอบสินค้า ครั้งที่ {pk}", author="ระบบจัดการคลังสินค้า (RFInv)")
    font_name, font_bold = register_thai_font()
    styles = getSampleStyleSheet()
    style_normal = ParagraphStyle('Normal_Thai', parent=styles['Normal'], fontName=font_name, fontSize=13)
    style_h2 = ParagraphStyle('H2_Thai', parent=styles['Heading2'], fontName=font_bold, fontSize=18, alignment=1)
    style_h3 = ParagraphStyle('H3_Thai', parent=styles['Heading3'], fontName=font_bold, fontSize=16, alignment=0)
    
    elements = []
    elements.append(Paragraph('รายงานสรุปผลการตรวจสอบสินค้า', style_h2))
    elements.append(Spacer(1, 10))
    
    # ข้อมูลการตรวจ
    info = f"<b>สถานที่ตรวจสอบ:</b> {inspection.location.name}<br/>"
    info += f"<b>วันที่ตรวจสอบ:</b> {timezone.localtime(inspection.inspected_at).strftime('%d/%m/%Y %H:%M')}<br/>"
    info += f"<b>ผู้ตรวจสอบ:</b> {inspection.inspected_by.get_full_name() or inspection.inspected_by.username}<br/><br/>"
    info += f"<b>สรุปยอด:</b> ควรมี {inspection.total_expected} รายการ, พบจริง {inspection.total_found} รายการ, หาย {inspection.total_missing} รายการ"
    elements.append(Paragraph(info, style_normal))
    elements.append(Spacer(1, 20))
    
    # คำนวณของหาย เกิน พบ
    # ดึงรายการสินค้าที่ควรจะมีในขณะนั้น (รวมสินค้าที่ถูกจำหน่ายออกไปแล้ว "หลังจาก" การตรวจสอบนี้ด้วย)
    expected_items = Inventory.objects.filter(
        Q(status='ACTIVE') | Q(status='DISPOSED', disposed_at__gte=inspection.inspected_at) | Q(status='DISPOSED', disposed_at__isnull=True),
        current_location=inspection.location
    )
    found_items = inspection.found_inventories.all()
    expected_ids = set(expected_items.values_list('id', flat=True))
    found_ids = set(found_items.values_list('id', flat=True))
    
    missing_ids = expected_ids - found_ids
    extra_ids = found_ids - expected_ids
    actual_found_ids = expected_ids & found_ids
    
    missing_items = Inventory.objects.filter(id__in=missing_ids).order_by('name')
    extra_items = Inventory.objects.filter(id__in=extra_ids).order_by('name')
    found_matched_items = Inventory.objects.filter(id__in=actual_found_ids).order_by('name')
    
    def build_table(items, empty_msg):
        #data = [['รูปภาพ', 'ID', 'ชื่อสินค้า', 'RFID Code']]
        data = [['รูปภาพ', 'ชื่อสินค้า', 'RFID Code']]
        if not items:
            data.append([empty_msg, '', '', ''])
            
        for item in items:
            img = Paragraph('<font color="#999999">ไม่มีรูป</font>', style_normal)
            if item.image and item.image.name:
                img_path = os.path.join(settings.MEDIA_ROOT, item.image.name)
                if os.path.exists(img_path):
                    img = Image(img_path, width=40, height=40)
            rfid = item.rfid_tag.rfid_code if item.rfid_tag else '-'
            
            name_text = item.name
            if item.status == 'DISPOSED':
                dt = timezone.localtime(item.disposed_at).strftime('%d/%m/%Y %H:%M') if item.disposed_at else '-'
                usr = (item.disposed_by.get_full_name() or item.disposed_by.username) if item.disposed_by else '-'
                name_text += f"<br/><font color='red'><b>[จำหน่ายออกแล้ว]</b><br/>วันที่: {dt}<br/>โดย: {usr}</font>"
                
            #data.append([img, str(item.id), Paragraph(name_text, style_normal), rfid])
            data.append([img, Paragraph(name_text, style_normal), rfid])
            
        #t = Table(data, colWidths=[2.5*cm, 1.5*cm, 9*cm, 5*cm])
        t = Table(data, colWidths=[2.5*cm, 10*cm, 4*cm])
        ts = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f1f1')),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (0, 1), (1, -1), 'CENTER'),
            ('ALIGN', (3, 1), (3, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTNAME', (0, 0), (-1, 0), font_bold),
        ]
        if not items:
            ts.extend([('SPAN', (0, 1), (-1, 1)), ('ALIGN', (0, 1), (0, 1), 'CENTER')])
            
        t.setStyle(TableStyle(ts))
        return t



    '''
    elements.append(Paragraph('<font color="#fd7e14">รายการสินค้าที่พบใหม่ (เกิน)</font>', style_h3))
    elements.append(Spacer(1, 5))
    elements.append(build_table(extra_items, 'ไม่มีสินค้าที่พบใหม่'))
    elements.append(Spacer(1, 15))
    '''

    elements.append(Paragraph('<font color="#198754">รายการสินค้าที่พบถูกต้อง</font>', style_h3))
    elements.append(Spacer(1, 5))
    elements.append(build_table(found_matched_items, 'ไม่มีสินค้าที่พบถูกต้อง'))
    
    elements.append(Paragraph('<font color="red">รายการสินค้าที่หาย (ไม่พบ)</font>', style_h3))
    elements.append(Spacer(1, 5))
    elements.append(build_table(missing_items, 'ไม่มีสินค้าที่หาย'))
    elements.append(Spacer(1, 15))

    #doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)
    doc.build(elements, canvasmaker=PageNumCanvas)
    return response

def generate_disposed_report(request):
    """ สร้างรายงานประวัติการจำหน่ายสินค้า """
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="disposed_report.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=A4, rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm,
                            title="รายงานสินค้าจำหน่ายออก (สูญหาย/ชำรุด)", author="ระบบจัดการคลังสินค้า (RFInv)")
    font_name, font_bold = register_thai_font()
    styles = getSampleStyleSheet()
    style_normal = ParagraphStyle('Normal_Thai', parent=styles['Normal'], fontName=font_name, fontSize=13)
    style_h2 = ParagraphStyle('H2_Thai', parent=styles['Heading2'], fontName=font_bold, fontSize=18, alignment=1)
    
    elements = []
    elements.append(Paragraph('รายงานสินค้าจำหน่ายออก (สูญหาย/ชำรุด)', style_h2))
    
    printed_by = request.user.get_full_name() or request.user.username
    printed_time = timezone.localtime(timezone.now()).strftime("%d/%m/%Y %H:%M")
    meta_info = f"<b>ผู้พิมพ์:</b> {printed_by} &nbsp;&nbsp;&nbsp;&nbsp; <b>เวลาพิมพ์:</b> {printed_time}"
    elements.append(Spacer(1, 5))
    elements.append(Paragraph(meta_info, style_normal))
    
    query = Inventory.objects.filter(status='DISPOSED')
    if start_date and end_date:
        try:
            from datetime import datetime
            sd = datetime.strptime(start_date, '%Y-%m-%d')
            ed = datetime.strptime(end_date, '%Y-%m-%d')
            query = query.filter(disposed_at__range=(sd, ed.replace(hour=23, minute=59, second=59)))
            elements.append(Spacer(1, 5))
            elements.append(Paragraph(f"<b>ช่วงวันที่จำหน่าย:</b> {start_date} ถึง {end_date}", style_normal))
        except ValueError:
            pass
            
    elements.append(Spacer(1, 10))
    
    data = [['รูปภาพ', 'ID', 'ชื่อสินค้า', 'วันที่จำหน่าย', 'ผู้จำหน่าย']]
    for item in query.order_by('-disposed_at'):
        dt = timezone.localtime(item.disposed_at).strftime('%d/%m/%Y %H:%M') if item.disposed_at else '-'
        usr = item.disposed_by.username if item.disposed_by else '-'
        
        img = Paragraph('<font color="#999999">ไม่มีรูป</font>', style_normal)
        if item.image and item.image.name:
            img_path = os.path.join(settings.MEDIA_ROOT, item.image.name)
            if os.path.exists(img_path):
                img = Image(img_path, width=40, height=40)
                
        data.append([img, str(item.id), Paragraph(item.name, style_normal), dt, usr])
        
    if query.count() == 0:
        data.append(['', '', 'ไม่พบข้อมูลในช่วงเวลานี้', '', ''])
        
    t = Table(data, colWidths=[2.5*cm, 1.5*cm, 6.5*cm, 3.5*cm, 4.0*cm])
    table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f1f1')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTNAME', (0, 0), (-1, 0), font_bold),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ALIGN', (0, 1), (1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]
    if query.count() == 0:
        table_style.extend([('SPAN', (2, 1), (-1, 1)), ('ALIGN', (2, 1), (2, 1), 'CENTER')])
        
    t.setStyle(TableStyle(table_style))
    elements.append(t)
    
    #doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)
    doc.build(elements, canvasmaker=PageNumCanvas)
    return response

def generate_product_report(request):
    """ สร้างและคืนค่ารายงาน PDF: ประวัติการตรวจสอบสินค้า (ใช้ ReportLab) """
    product_id = request.GET.get('product_id')
    
    if product_id == 'ALL':
        products = Inventory.objects.all().order_by('name')
    else:
        products = Inventory.objects.filter(id=product_id)
        
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="product_report.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=A4, rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm,
                            title="รายงานประวัติการตรวจสอบสินค้า", author="ระบบจัดการคลังสินค้า (RFInv)")
    font_name, font_bold = register_thai_font()
    styles = getSampleStyleSheet()
    
    style_normal = ParagraphStyle('Normal_Thai', parent=styles['Normal'], fontName=font_name, fontSize=13, wordWrap='CJK')
    style_h2 = ParagraphStyle('H2_Thai', parent=styles['Heading2'], fontName=font_bold, fontSize=18, alignment=1, wordWrap='CJK')
    style_h3 = ParagraphStyle('H3_Thai', parent=styles['Heading3'], fontName=font_bold, fontSize=16, alignment=1, wordWrap='CJK')
    style_h4 = ParagraphStyle('H4_Thai', parent=styles['Heading4'], fontName=font_bold, fontSize=14, textColor=colors.HexColor('#198754'), wordWrap='CJK')

    elements = []
    elements.append(Paragraph('ระบบจัดการคลังสินค้า (RFInv)', style_h2))
    elements.append(Paragraph('รายงานประวัติการตรวจสอบสินค้า', style_h3))
    
    printed_by = request.user.get_full_name() or request.user.username
    printed_time = timezone.localtime(timezone.now()).strftime("%d/%m/%Y %H:%M")
    
    meta_info = f"<b>ผู้พิมพ์:</b> {printed_by} &nbsp;&nbsp;&nbsp;&nbsp; <b>เวลาพิมพ์:</b> {printed_time}"
    elements.append(Paragraph(meta_info, style_normal))
    elements.append(Spacer(1, 10))
    
    for i, prod in enumerate(products):
        if i > 0:
            elements.append(PageBreak())
            
        img = Paragraph('<font color="#999999">ไม่มีรูป</font>', style_normal)
        if prod.image and prod.image.name:
            img_path = os.path.join(settings.MEDIA_ROOT, prod.image.name)
            if os.path.exists(img_path):
                img = Image(img_path, width=80, height=80)
        
        rfid = prod.rfid_tag.rfid_code if prod.rfid_tag else "-"
        loc = prod.current_location.name if prod.current_location else "-"
        info_text = f"<b>RFID Code:</b> {rfid}<br/><b>สถานที่ปัจจุบัน:</b> {loc}"
        if prod.status == 'DISPOSED':
            dt = timezone.localtime(prod.disposed_at).strftime('%d/%m/%Y %H:%M') if prod.disposed_at else '-'
            usr = (prod.disposed_by.get_full_name() or prod.disposed_by.username) if prod.disposed_by else '-'
            info_text += f"<br/><br/><font color='red'><b>[จำหน่ายออกแล้ว]</b></font><br/><b>วันที่จำหน่าย:</b> {dt}<br/><b>ผู้จำหน่าย:</b> {usr}"        
        info_cell = [Paragraph(prod.name, style_h4), Spacer(1, 5), Paragraph(info_text, style_normal)]
        
        info_table = Table([[img, info_cell]], colWidths=[3*cm, 13*cm])
        info_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (1, 0), (1, 0), 15),
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f9f9f9')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#dddddd')),
            ('PADDING', (0,0), (-1,-1), 10),
            ('FONTNAME', (0, 0), (-1, -1), font_name),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 15))
        
        elements.append(Paragraph('ประวัติการตรวจสอบ (เรียงจากปัจจุบันไปอดีต)', ParagraphStyle('HistoryTitle', parent=style_normal, fontName=font_bold)))
        elements.append(Spacer(1, 5))
        
        history_data = [['วันเวลาตรวจสอบ', 'ผู้ตรวจสอบ', 'ตำแหน่งที่ตรวจสอบ']]
        history_records = prod.inspections.all().order_by('-inspected_at')
        
        if not history_records:
            history_data.append(['ไม่มีประวัติการตรวจสอบ', '', ''])
        
        for history in history_records:
            checked_time = timezone.localtime(history.inspected_at).strftime("%d/%m/%Y %H:%M")
            checked_by = history.inspected_by.get_full_name() or history.inspected_by.username
            loc_name = history.location.name if history.location else ""
            history_data.append([
                Paragraph(checked_time, style_normal),
                Paragraph(checked_by, style_normal),
                Paragraph(loc_name, style_normal)
            ])
            
        t = Table(history_data, colWidths=[4.5*cm, 5.5*cm, 6*cm])
        table_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f1f1')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
            ('FONTNAME', (0, 0), (-1, 0), font_bold),
            ('FONTNAME', (0, 1), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]
        if not history_records:
            table_style.extend([('SPAN', (0, 1), (2, 1)), ('ALIGN', (0,1), (0,1), 'CENTER')])
            
        t.setStyle(TableStyle(table_style))
        elements.append(t)
        elements.append(Spacer(1, 20))
        
    doc.build(elements, canvasmaker=PageNumCanvas)
    return response
