from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import *
from BackButtonWindow import BackButtonWindow
import sys
import time
import cv2
import numpy as np

class CamWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('CamWindow')

        self.image_label = QLabel(self)
        self.image_label.setFixedSize(640, 480) 

        # 수집된 이미지를 표시할 QTimer 생성
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

        # OpenCV 웹캠 초기화
        self.cap = cv2.VideoCapture(0)

        # GUI 레이아웃 설정
        layout = QVBoxLayout(self)
        layout.addWidget(self.image_label)
        self.setLayout(layout)

    def start_camera(self):
        # QTimer를 사용하여 매 프레임마다 이미지 업데이트
        self.timer.start(30)  

    def stop_camera(self):
        # QTimer 중지
        self.timer.stop()

    def update_frame(self):
        # 웹캠 프레임 읽기
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.resize(frame, (1280, 720))
            # snip = frame[500:720, :]
            snip = frame[:, :]

            # Threshold -> Only Black Line
            gray = cv2.cvtColor(snip, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 90, 255, cv2.THRESH_BINARY)

            # Noise Canceling
            kernel = np.ones((5, 5), np.uint8)
            thresh = cv2.dilate(thresh, kernel, iterations=1)

            # Edge Detection
            edges = cv2.Canny(thresh, 50, 150)

            lines = cv2.HoughLines(edges, 1, np.pi / 180, 100)

            left_lines = []
            right_lines = []

            if lines is not None:
                for line in lines:
                    rho, theta = line[0]
                    if theta < np.pi / 2:
                        left_lines.append((rho, theta))
                    else:
                        right_lines.append((rho, theta))

            if len(left_lines) > 0:
                left_rho, left_theta = np.median(left_lines, axis=0)
                a = np.cos(left_theta)
                b = np.sin(left_theta)
                x0 = a * left_rho
                y0 = b * left_rho
                x1 = int(x0 + 400 * (-b))
                y1 = int(y0 + 400 * (a))
                x2 = int(x0 - 600 * (-b))
                y2 = int(y0 - 600 * (a))
                cv2.line(snip, (x1, y1), (x2, y2), (0, 0, 255), 2)
                cv2.putText(snip, 'Left line', (x2, y2), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

            if len(right_lines) > 0:
                right_rho, right_theta = np.median(right_lines, axis=0)
                a = np.cos(right_theta)
                b = np.sin(right_theta)
                x0 = a * right_rho
                y0 = b * right_rho
                x1 = int(x0 + 400 * (-b))
                y1 = int(y0 + 400 * (a))
                x2 = int(x0 - 600 * (-b))
                y2 = int(y0 - 600 * (a))
                cv2.line(snip, (x1, y1), (x2, y2), (255, 0, 0), 2)
                cv2.putText(snip, 'Right line', (x2, y2), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

            # Find the contour
            contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)


            # Find the contour with the approximate center
            center_contour = None
            min_distance = float('inf')
            for contour in contours:
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cX = int(M["m10"] / M["m00"])
                    cY = int(M["m01"] / M["m00"])
                    distance = abs(cX - snip.shape[1] // 2)
                    if distance < min_distance:
                        center_contour = contour
                        min_distance = distance

            # Draw the center contour
            if center_contour is not None:
                cv2.drawContours(snip, [center_contour], -1, (0, 255, 0), 2)

                # Calculate the center coordinates
                M = cv2.moments(center_contour)
                if M["m00"] != 0:
                    cX = int(M["m10"] / M["m00"])
                    cY = int(M["m01"] / M["m00"])
                    cv2.circle(snip, (cX, cY), 5, (0, 255, 0), -1)
                    # cv2.putText(snip, 'center x value:' + str(cX) , (cX, cY), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    # screen size : 1280x720    ->  1280x220

                    snip_width = 1280
                    snip_left_width = snip_width / 2 - 50
                    snip_right_width = snip_width / 2 + 50

                    if (cX < snip_left_width):
                        direction = 'L'
                    elif (cX > snip_right_width):
                        direction = 'R'
                    elif (cX >= snip_left_width and cX <= snip_right_width):
                        direction = 'F'

                    cv2.putText(snip, 'direction:' + direction , (cX, cY), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # OpenCV BGR 이미지를 RGB로 변환하여 QImage로 변환
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, c = rgb_image.shape
            q_image = QImage(rgb_image.data, w, h, w * c, QImage.Format_RGB888)

            # QLabel에 QImage 표시
            self.image_label.setPixmap(QPixmap.fromImage(q_image))



class ButtonWindow(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        # QWidget.__init__(self, parent)
        self.setWindowTitle('Button Window')
        self.show()
        # 서빙로봇 MOVE 버튼 생성
        self.moveButton1 = QPushButton('1번')
        self.moveButton1.clicked.connect(self.move)
        self.moveButton2 = QPushButton('2번')
        self.moveButton2.clicked.connect(self.move)
        self.moveButton3 = QPushButton('3번')
        self.moveButton3.clicked.connect(self.move)
        self.moveButton4 = QPushButton('4번')
        self.moveButton4.clicked.connect(self.move)
        groupBox1 = QGroupBox('group1', self)
        self.buttonLayout1 = QHBoxLayout(groupBox1)
        self.buttonLayout1.addWidget(self.moveButton1)
        self.buttonLayout1.addWidget(self.moveButton2)
        self.buttonLayout1.addWidget(self.moveButton3)
        self.buttonLayout1.addWidget(self.moveButton4)

        self.moveButton5 = QPushButton('5번')
        self.moveButton5.clicked.connect(self.move)
        self.moveButton6 = QPushButton('6번')
        self.moveButton6.clicked.connect(self.move)
        self.moveButton7 = QPushButton('7번')
        self.moveButton7.clicked.connect(self.move)
        self.moveButton8 = QPushButton('8번')
        self.moveButton8.clicked.connect(self.move)
        groupBox2 = QGroupBox('group2', self)
        self.buttonLayout2 = QHBoxLayout(groupBox2)
        self.buttonLayout2.addWidget(self.moveButton5)
        self.buttonLayout2.addWidget(self.moveButton6)
        self.buttonLayout2.addWidget(self.moveButton7)
        self.buttonLayout2.addWidget(self.moveButton8)

        self.moveButton9 = QPushButton('9번')
        self.moveButton9.clicked.connect(self.move)
        self.moveButton10 = QPushButton('10번')
        self.moveButton10.clicked.connect(self.move)
        self.moveButton11 = QPushButton('11번')
        self.moveButton11.clicked.connect(self.move)
        self.moveButton12 = QPushButton('12번')
        self.moveButton12.clicked.connect(self.move)
        groupBox3 = QGroupBox('group3', self)
        self.buttonLayout3 = QHBoxLayout(groupBox3)
        self.buttonLayout3.addWidget(self.moveButton9)
        self.buttonLayout3.addWidget(self.moveButton10)
        self.buttonLayout3.addWidget(self.moveButton11)
        self.buttonLayout3.addWidget(self.moveButton12)

        self.moveButton13 = QPushButton('13번')
        self.moveButton13.clicked.connect(self.move)
        self.moveButton14 = QPushButton('14번')
        self.moveButton14.clicked.connect(self.move)
        self.moveButton15 = QPushButton('15번')
        self.moveButton15.clicked.connect(self.move)
        self.moveButton16 = QPushButton('16번')
        self.moveButton16.clicked.connect(self.move)
        groupBox4 = QGroupBox('group4', self)
        self.buttonLayout4 = QHBoxLayout(groupBox4)
        self.buttonLayout4.addWidget(self.moveButton13)
        self.buttonLayout4.addWidget(self.moveButton14)
        self.buttonLayout4.addWidget(self.moveButton15)
        self.buttonLayout4.addWidget(self.moveButton16)

        self.moveButton17 = QPushButton('17번')
        self.moveButton17.clicked.connect(self.move)
        self.moveButton18 = QPushButton('18번')
        self.moveButton18.clicked.connect(self.move)
        self.moveButton19 = QPushButton('19번')
        self.moveButton19.clicked.connect(self.move)
        self.moveButton20 = QPushButton('20번')
        self.moveButton20.clicked.connect(self.move)
        groupBox5 = QGroupBox('group5', self)
        self.buttonLayout5 = QHBoxLayout(groupBox5)
        self.buttonLayout5.addWidget(self.moveButton17)
        self.buttonLayout5.addWidget(self.moveButton18)
        self.buttonLayout5.addWidget(self.moveButton19)
        self.buttonLayout5.addWidget(self.moveButton20)

        # 종료 버튼
        self.closeButton = QPushButton('종료')
        self.closeButton.clicked.connect(self.onClickClose)

        layout = QVBoxLayout()
        layout.addWidget(groupBox1)
        layout.addWidget(groupBox2)
        layout.addWidget(groupBox3)
        layout.addWidget(groupBox4)
        layout.addWidget(groupBox5)
        layout.addWidget(self.closeButton)

        self.setLayout(layout)
        self.resize(500, 500)

    def onClickClose(self):
        self.close()
        

    def move(self):
        self.camWindow = CamWindow()
        self.camWindow.start_camera()
        self.camWindow.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)

    buttonWindow = ButtonWindow()
    buttonWindow.show()

    app.exec_()