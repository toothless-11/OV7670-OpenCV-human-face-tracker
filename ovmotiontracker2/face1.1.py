import serial

import numpy as np
import cv2

# ===== 串口参数 =====
PORT = 'COM3'          
BAUD = 500000          # 必须和 Arduino 一致
ser = serial.Serial(PORT, BAUD, timeout=0.05)

# ===== 图像参数 =====
WIDTH = 120
HEIGHT = 80
FRAME_SIZE = WIDTH * HEIGHT
center_x = WIDTH/2 #横坐标中心

# ===== 协议常量 =====
VERSION = 0x10
COMMAND_NEW_FRAME = 0x01 | VERSION   #新帧命令

buffer = bytearray()
collecting = False
frame = bytearray()

#人脸识别
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)
clip = 4 #间隔clip帧采集一次人脸
count = 0
num = 0

print("Start receiving...")


while True:
    data = ser.read(FRAME_SIZE)
    if data:
        buffer.extend(data)

    i = 0
    while i < len(buffer):
        b = buffer[i]

        # ---------- 命令解析 ----------
        if not collecting and b == 0x00:
            # 至少需要：0x00 + length + command
            if i + 2 >= len(buffer):
                break

            length = buffer[i + 1]
            # 整条命令还没收全
            if i + 2 + length >= len(buffer):
                break

            cmd = buffer[i + 2]

            # 新帧命令
            if cmd == COMMAND_NEW_FRAME:
                collecting = True
                frame.clear()

            # 跳过：0x00 + length + payload + checksum
            i += 2 + length + 1
            continue

        # ---------- 图像数据 ----------
        if collecting:
            #frame 用来检测；img用来显示
            frame.append(b)
            flag = False
            #采集满了，就显示
            if len(frame) == FRAME_SIZE:
                count += 1
                num += 1
                print(num)
                # bytes → numpy 灰度图（这是“检测用 frame”）
                frame_np = np.frombuffer(bytes(frame), dtype=np.uint8).reshape((WIDTH,HEIGHT))
                frame_np = cv2.convertScaleAbs(frame_np, alpha=3, beta=5) #对比度+亮度调节，帮助人脸识别
                # 直方图均衡
                frame_np = cv2.equalizeHist(frame_np)

                # 轻度去噪
                frame_np = cv2.GaussianBlur(frame_np, (3, 3), 0)

                frame_np = cv2.rotate(frame_np, cv2.ROTATE_90_CLOCKWISE)


                # 2. 人脸检测（只用 frame_np）
                if count == 1:
                    faces = face_cascade.detectMultiScale(
                        frame_np,
                        scaleFactor=1.1,
                        minNeighbors=0, #灵敏度最高状态
                        minSize=(20, 20)
                    )
                    if len(faces) > 0:
                        print(count)
                        flag = True #表示检测到人脸
                elif count == clip:
                    count = 0
                
                #  转 BGR 仅用于显示
                img = cv2.cvtColor(frame_np, cv2.COLOR_GRAY2BGR)

                if flag:
                    #  画框
                    x, y, w, h =faces[0]
                    cv2.rectangle(img, (x, y), (x+w, y+h), (0,255,0), 1)
                    #  发送电机指令
                    if abs(x + w//2 - center_x) > 20:
                        ser.write(bytes([100 if x +w//2 < center_x else 99]))
                        print("000000000")


                # 5. 放大+裁掉丢包部分+显示
                img = cv2.resize(img, (WIDTH*2, HEIGHT*2), interpolation=cv2.INTER_NEAREST)
                img = img[20:,:]
                cv2.imshow("OV7670", img)
                cv2.waitKey(1)

                

                collecting = False
                frame.clear()

        i += 1

    # 清掉已处理的数据
    buffer = buffer[i:]

    if cv2.waitKey(1) & 0xFF == 27:  # 按下ESC 退出
        break

ser.close()
cv2.destroyAllWindows()
