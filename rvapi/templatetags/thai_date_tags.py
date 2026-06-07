from django import template
from datetime import datetime

register = template.Library()

# รายชื่อเดือนภาษาไทยแบบย่อและแบบเต็ม
THAI_MONTHS_SHORT = ["", "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]
THAI_MONTHS_FULL = ["", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]

@register.filter(name='to_thai_date')
def to_thai_date(value, format_type="short_time"):
    if not value:
        return "-"
    
    if isinstance(value, datetime):
        dt = value
    else:
        try:
            dt = datetime.fromisoformat(str(value))
        except ValueError:
            return value

    # เตรียมข้อมูลพื้นฐาน
    day = dt.day
    month_num = dt.month
    year_be = dt.year + 543
    time_str = dt.strftime('%H:%M')

    # ส่วนลดรูปสำหรับแบบตัวเลข (เช่น 07/06/2569)
    day_padded = f"{day:02d}"
    month_padded = f"{month_num:02d}"

    # เลือกรูปแบบตาม format_type ที่ส่งมา
    if format_type == "short":
        # ผลลัพธ์: 07/06/2569
        return f"{day_padded}/{month_padded}/{year_be}"
        
    elif format_type == "short_time":
        # ผลลัพธ์: 07/06/2569 22:19 (ค่าเริ่มต้นถ้าไม่ใส่อะไรเลย)
        return f"{day_padded}/{month_padded}/{year_be} {time_str}"
        
    elif format_type == "full":
        # ผลลัพธ์: 7 มิถุนายน 2569
        return f"{day} {THAI_MONTHS_FULL[month_num]} {year_be}"
        
    elif format_type == "full_time":
        # ผลลัพธ์: 7 มิถุนายน 2569 เวลา 22:19 น.
        return f"{day} {THAI_MONTHS_FULL[month_num]} {year_be} เวลา {time_str} น."
        
    elif format_type == "month_short_time":
        # ผลลัพธ์: 7 มิ.ย. 2569 22:19
        return f"{day} {THAI_MONTHS_SHORT[month_num]} {year_be} {time_str}"

    return f"{day_padded}/{month_padded}/{year_be} {time_str}"

'''
	แบบย่อ	{{ item.last_seen_at|to_thai_date:"short" }}07/06/2569
	แบบย่อ + เวลา{{ item.last_seen_at|to_thai_date:"short_time" }}07/06/2569 22:19
    แบบเดือนย่อ + เวลา{{ item.last_seen_at|to_thai_date:"month_short_time" }}7 มิ.ย. 2569 22:19 
	แบบเต็ม{{ item.last_seen_at|to_thai_date:"full" }}7 มิถุนายน 2569 
	แบบเต็ม + เวลา{{ item.last_seen_at|to_thai_date:"full_time" }}7 มิถุนายน 2569 เวลา 22:19 น.
	default{{ item.last_seen_at\|to_thai_date }} 07/06/2569 22:19 
'''    