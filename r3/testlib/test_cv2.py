import cv2

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("ไม่พบกล้อง หรือเปิดกล้องไม่ได้")
else:
    ret, frame = cap.read()
    if not ret:
        print("ไม่สามารถอ่านภาพจากกล้องได้")
    else:
        cv2.imwrite("test_cam.jpg", frame)
        print("ทดลองถ่ายภาพสำเร็จ: test_cam.jpg")
cap.release()