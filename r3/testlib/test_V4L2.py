import cv2
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
if not cap.isOpened():
    print('ไม่พบกล้อง หรือเปิดกล้องไม่ได้')
else:
    print('cap opened')
    for i in range(5):
        ret, frame = cap.read()
        print('ret:', ret, 'frame:', None if frame is None else frame.shape)
    cap.release()