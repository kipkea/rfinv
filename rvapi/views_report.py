import os
from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse
from django.utils import timezone

# ReportLab imports
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont

from .models import Inventory, Location, Inspection

# ฟังก์ชันสำหรับเพิ่มเลขหน้าลงในเอกสาร ReportLab
def add_page_number(canvas, doc):
    canvas.saveState()
    
    # 1. วาดลายน้ำ (Watermark)
    # แนะนำให้นำไฟล์รูปโลโก้ (ควรเป็น PNG ที่ปรับความโปร่งใส/ทำสีจางมาแล้ว) ไปวางไว้ในโฟลเดอร์ assets
    watermark_path = os.path.join(settings.BASE_DIR, 'assets', 'watermark0.png')
    if os.path.exists(watermark_path):
        img_width = 12 * cm
        img_height = 12 * cm
        # คำนวณพิกัดให้รูปภาพอยู่กึ่งกลางหน้ากระดาษ A4
        x = (A4[0] - img_width) / 2
        y = (A4[1] - img_height) / 2
        canvas.drawImage(watermark_path, x, y, width=img_width, height=img_height, mask='auto')

    # 2. วาดเลขหน้า
    page_num = canvas.getPageNumber()
    text = f"หน้า {page_num}"
    try:
        canvas.setFont('THSarabun', 11)
    except Exception:
        canvas.setFont('Helvetica', 11)
    canvas.drawRightString(A4[0] - 1.5*cm, 1.5*cm, text)
    canvas.restoreState()

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
    
    doc = SimpleDocTemplate(response, pagesize=A4, rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
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
        items = loc.current_items.all().order_by('name')
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
        
    doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)
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
    
    doc = SimpleDocTemplate(response, pagesize=A4, rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
    font_name, font_bold = register_thai_font()
    styles = getSampleStyleSheet()
    
    style_normal = ParagraphStyle('Normal_Thai', parent=styles['Normal'], fontName=font_name, fontSize=13, wordWrap='CJK')
    style_h2 = ParagraphStyle('H2_Thai', parent=styles['Heading2'], fontName=font_bold, fontSize=18, alignment=1, wordWrap='CJK')
    style_h3 = ParagraphStyle('H3_Thai', parent=styles['Heading3'], fontName=font_bold, fontSize=16, alignment=1, wordWrap='CJK')
    style_h4 = ParagraphStyle('H4_Thai', parent=styles['Heading4'], fontName=font_bold, fontSize=14, textColor=colors.HexColor('#198754'), wordWrap='CJK')

    elements = []
    elements.append(Paragraph('ระบบจัดการคลังสินค้า (RFInv)', style_h2))
    elements.append(Paragraph('รายงานประวัติการตรวจสอบและพิกัดสินค้า', style_h3))
    
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
        
    doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)
    return response
