import matplotlib.pyplot as plt
import numpy as np

# --- กำหนดข้อมูล (แก้ไขตรงนี้ได้ตามผลการทดลองจริง) ---
items = np.array([100, 200, 300, 400, 500]) # จำนวนสินค้า (แกน X)

# เวลาที่ใช้ (วินาที)
time_barcode = items * 3.0      # Barcode: สมมติว่า 3 วินาที/ชิ้น (กราฟชันขึ้นเรื่อยๆ)
time_rfid = np.array([5, 8, 10, 12, 15]) # RFID: อ่านทีละเยอะๆ เวลาเพิ่มขึ้นน้อยมาก

# --- วาดกราฟ ---
plt.figure(figsize=(8, 5)) # กำหนดขนาดภาพ
plt.plot(items, time_barcode, marker='o', linestyle='-', label='Barcode System', color='#D9534F')
plt.plot(items, time_rfid, marker='s', linestyle='--', label='RFID System', color='#428BCA')

# ตกแต่งกราฟ
plt.title('Comparison of Reading Time: RFID vs Barcode', fontsize=14, fontweight='bold')
plt.xlabel('Number of Items (pcs)', fontsize=12)
plt.ylabel('Processing Time (seconds)', fontsize=12)
plt.legend(fontsize=12)
plt.grid(True, linestyle='--', alpha=0.6)

# บันทึกไฟล์
plt.tight_layout()
plt.savefig('comparison_graph.png', dpi=300)
print("สร้างไฟล์ comparison_graph.png เรียบร้อยแล้ว")
plt.show()