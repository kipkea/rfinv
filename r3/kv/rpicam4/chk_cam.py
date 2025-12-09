import cv2
import sys

# ----------------------------------------------------------------------
# การตั้งค่าพารามิเตอร์เบื้องต้น
# ----------------------------------------------------------------------

# ดัชนีกล้อง (Camera Index):
# 0: มักจะเป็นกล้อง USB ตัวแรก หรือกล้อง Pi Camera Module (บนระบบปฏิบัติการสมัยใหม่)
# 1, 2, ... : กล้องตัวที่สอง, ตัวที่สาม, ...
CAMERA_INDEX = 0 
WINDOW_NAME = 'Raspberry Pi Camera Check - Press Q to Exit'
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# ----------------------------------------------------------------------
# อัลกอริทึม: การตรวจสอบและเริ่มการทำงานของกล้อง
# ----------------------------------------------------------------------

def run_camera_check():
    """
    ฟังก์ชันหลักในการตรวจสอบและแสดงผลสตรีมจากกล้อง
    """
    print(f"Attempting to open camera with index: {CAMERA_INDEX}...")
    
    # 1. สร้างวัตถุ VideoCapture
    # cv2.CAP_V4L2 เป็น backend ที่ดีสำหรับ Linux (Raspberry Pi)
    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_V4L2)

    # 2. ตรวจสอบสถานะการเปิดกล้อง
    if not cap.isOpened():
        print(f"Error: Failed to open camera at index {CAMERA_INDEX}.")
        print("Please check camera connection and permissions.")
        # ลองดัชนีกล้องอื่น ๆ ที่อาจเป็นไปได้
        cap.release()
        print("Attempting to try camera index 1...")
        cap = cv2.VideoCapture(1, cv2.CAP_V4L2)
        if not cap.isOpened():
            print("Error: Failed to open camera at index 1 as well. Exiting.")
            sys.exit(1)
        else:
            print("Successfully opened camera at index 1.")
            
    else:
        print(f"Camera opened successfully with index {CAMERA_INDEX}.")
        
    # 3. ตั้งค่าคุณสมบัติของกล้อง (เพื่อประสิทธิภาพที่ดีขึ้นบน RPi)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    print(f"Set resolution to {FRAME_WIDTH}x{FRAME_HEIGHT}.")

    # 4. วนลูปอ่านและแสดงเฟรมภาพ
    print("Starting camera stream. Press 'Q' to stop.")
    
    try:
        while True:
            # อ่านเฟรมภาพ
            ret, frame = cap.read()

            # ตรวจสอบว่าอ่านเฟรมได้สำเร็จหรือไม่
            if not ret:
                print("Can't receive frame (stream end?). Exiting...")
                break

            # แสดงผลเฟรม
            cv2.imshow(WINDOW_NAME, frame)

            # ตรวจสอบการกดปุ่ม 'q' เพื่อออก
            # cv2.waitKey(1) คือการรอ 1 มิลลิวินาที
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    except KeyboardInterrupt:
        print("Interrupted by user (Ctrl+C).")
    finally:
        # 5. ปลดปล่อยทรัพยากรเมื่อจบการทำงาน
        cap.release()
        cv2.destroyAllWindows()
        print("Camera stream ended and resources released.")

if __name__ == '__main__':
    run_camera_check()