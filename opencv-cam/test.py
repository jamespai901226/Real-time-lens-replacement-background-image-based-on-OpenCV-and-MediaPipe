from PyQt5 import QtCore, QtGui, QtWidgets
from PIL import Image
import sys
import cv2
import numpy as np
import mediapipe as mp
from PyQt5.QtWidgets import QFileDialog, QMessageBox

class Ui_MainWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("cam bg rm")  # 設置窗口標題

        self.timer_camera = QtCore.QTimer()  # 定義定時器，用於控制顯示視頻的幀率
        self.cap = cv2.VideoCapture()  # 視頻流
        self.CAM_NUM = 0  # 為0時表示視頻流來自筆記本內置攝像頭
        self.bg = None  # 背景圖片
        self.use_bg = False  # 是否使用背景圖片
        self.flip_image = False  # 是否翻轉影像

        self.mp_selfie_segmentation = mp.solutions.selfie_segmentation.SelfieSegmentation(model_selection=1)
        self.set_ui()  # 初始化程序界面
        self.slot_init()  # 初始化槽函數

        # 顯示歡迎訊息彈窗
        self.show_welcome_message()

    '''程序界面佈局'''

    def set_ui(self):
        self.__layout_main = QtWidgets.QHBoxLayout()  # 總佈局
        self.__layout_fun_button = QtWidgets.QVBoxLayout()  # 按鍵佈局
        self.__layout_data_show = QtWidgets.QVBoxLayout()  # 數據(視頻)顯示佈局
        self.button_open_camera = QtWidgets.QPushButton('開關相機')  # 建立用於打開攝像頭的按鍵
        self.button_import_bg = QtWidgets.QPushButton('匯入背景')  # 建立用於匯入背景的按鍵
        self.button_sample_bg = QtWidgets.QPushButton('選擇範例背景')  # 建立用於選擇範例背景的按鍵
        self.button_toggle_bg = QtWidgets.QPushButton('開啟背景')  # 建立用於切換背景的按鍵
        self.button_flip_image = QtWidgets.QPushButton('影像翻轉')  # 建立用於影像翻轉的按鍵
        self.button_close = QtWidgets.QPushButton('退出')  # 建立用於退出程序的按鍵
        self.button_open_camera.setMinimumHeight(50)  # 設置按鍵大小
        self.button_import_bg.setMinimumHeight(50)
        self.button_sample_bg.setMinimumHeight(50)
        self.button_toggle_bg.setMinimumHeight(50)
        self.button_flip_image.setMinimumHeight(50)
        self.button_close.setMinimumHeight(50)

        self.button_close.move(10, 100)  # 移動按鍵
        '''信息顯示'''
        self.label_show_camera = QtWidgets.QLabel()  # 定義顯示視頻的Label
        self.label_show_camera.setFixedSize(640, 480)  # 給顯示視頻的Label設置大小為641x481
        self.label_show_camera.setStyleSheet('''QWidget{border-radius:7px;background-color:#d3d3d3;}''')  # 設置視頻顯示區域背景色
        '''把按鍵加入到按鍵佈局中'''
        self.__layout_fun_button.addWidget(self.button_open_camera)  # 把打開攝像頭的按鍵放到按鍵佈局中
        self.__layout_fun_button.addWidget(self.button_import_bg)  # 把匯入背景的按鍵放到按鍵佈局中
        self.__layout_fun_button.addWidget(self.button_sample_bg)  # 把選擇範例背景的按鍵放到按鍵佈局中
        self.__layout_fun_button.addWidget(self.button_toggle_bg)  # 把切換背景的按鍵放到按鍵佈局中
        self.__layout_fun_button.addWidget(self.button_flip_image)  # 把影像翻轉的按鍵放到按鍵佈局中
        self.__layout_fun_button.addWidget(self.button_close)  # 把退出程序的按鍵放到按鍵佈局中
        '''把某些控件加入到總佈局中'''
        self.__layout_main.addLayout(self.__layout_fun_button)  # 把按鍵佈局加入到總佈局中
        self.__layout_main.addWidget(self.label_show_camera)  # 把用於顯示視頻的Label加入到總佈局中
        '''總佈局佈置好後就可以把總佈局作為參數傳入下面函數'''
        self.setLayout(self.__layout_main)  # 到這步才會顯示所有控件

    '''初始化所有槽函數'''

    def slot_init(self):
        self.button_open_camera.clicked.connect(self.button_open_camera_clicked)  # 若該按鍵被點擊，則調用button_open_camera_clicked()
        self.button_import_bg.clicked.connect(self.import_bg_image)  # 若該按鍵被點擊，則調用import_bg_image()
        self.button_sample_bg.clicked.connect(self.select_sample_bg)  # 若該按鍵被點擊，則調用select_sample_bg()
        self.button_toggle_bg.clicked.connect(self.toggle_bg)  # 若該按鍵被點擊，則調用toggle_bg())
        self.button_flip_image.clicked.connect(self.flip_image_clicked)  # 若該按鍵被點擊，則調用flip_image_clicked()
        self.timer_camera.timeout.connect(self.show_camera)  # 若定時器結束，則調用show_camera()
        self.button_close.clicked.connect(self.close)  # 若該按鍵被點擊，則調用close()，注意這個close是父類QtWidgets.QWidget自帶的，會關閉程序

    '''顯示歡迎訊息彈窗'''

    def show_welcome_message(self):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)
        msg.setText("歡迎使用自動去背景程式\n先按開啟相機後選擇背景圖片，最後再按開啟背景套用。\n僅可使用jpg圖片。\n所有彈窗可直接按OK關閉或等待數秒自動關閉。\n本彈窗將於10秒後自動關閉。")
        msg.setWindowTitle("歡迎")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.button(QMessageBox.Ok).animateClick(10000)  # 自動關閉訊息框
        msg.exec_()

    '''槽函數之一'''

    def button_open_camera_clicked(self):
        if self.timer_camera.isActive() == False:  # 若定時器未啟動
            flag = self.cap.open(self.CAM_NUM, cv2.CAP_DSHOW)  # 參數是0，表示打開筆記本的內置攝像頭，參數是視頻文件路徑則打開視頻
            if flag == False:  # flag表示open()成不成功
                self.show_message("請檢查相機於電腦是否連接正確")
            else:
                self.timer_camera.start(30)  # 定時器開始計時30ms，結果是每過30ms從攝像頭中取一幀顯示
                self.button_open_camera.setText('關閉相機')
                self.show_message("相機已開啟")
        else:
            self.timer_camera.stop()  # 關閉定時器
            self.cap.release()  # 釋放視頻流
            self.label_show_camera.clear()  # 清空視頻顯示區域
            self.button_open_camera.setText('開關相機')
            self.show_message("相機已關閉")

    def import_bg_image(self):
        fname, _ = QFileDialog.getOpenFileName(self, '選擇背景圖片', '', 'Image files (*.jpg *.png)')
        if fname:
            self.bg = Image.open(fname)
            self.bg = self.bg.resize((640, 480))  # 調整背景圖像的大小
            self.bg = np.array(self.bg)  # 轉換為NumPy數組
            self.show_message("背景圖片已加載")

    def select_sample_bg(self):
        samples = ["sample/sample1.jpg", "sample/sample2.jpg", "sample/sample3.jpg", "sample/sample4.jpg", "sample/sample5.jpg"]
        items = ["範例背景1", "範例背景2", "範例背景3", "範例背景4", "範例背景5"]
        item, ok = QtWidgets.QInputDialog.getItem(self, "選擇範例背景", "範例背景列表:", items, 0, False)
        if ok and item:
            index = items.index(item)
            fname = samples[index]
            self.bg = Image.open(fname)
            self.bg = self.bg.resize((640, 480))  # 調整背景圖像的大小
            self.bg = np.array(self.bg)  # 轉換為NumPy數組
            self.show_message("範例背景圖片已加載")

    def toggle_bg(self):
        self.use_bg = not self.use_bg
        if self.use_bg:
            self.button_toggle_bg.setText('關閉背景')
            self.show_message("背景已開啟")
        else:
            self.button_toggle_bg.setText('開啟背景')
            self.show_message("背景已關閉")

    def flip_image_clicked(self):
        self.flip_image = not self.flip_image
        if self.flip_image:
            self.show_message("影像翻轉已開啟")
        else:
            self.show_message("影像翻轉已關閉")

    def show_message(self, message):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.button(QMessageBox.Ok).animateClick(5000)  # 自動關閉訊息框
        msg.exec_()

    def show_camera(self):
        flag, self.image = self.cap.read()  # 從視頻流中讀取
        if self.flip_image:
            self.image = cv2.flip(self.image, 1)
        show = cv2.resize(self.image, (640, 480))  # 把讀到的幀的大小重新設置為 640x480
        show_rgb = cv2.cvtColor(show, cv2.COLOR_BGR2RGB)  # 視頻色彩轉換回RGB，這樣才是現實的顏色

        results = self.mp_selfie_segmentation.process(show_rgb)
        condition = np.stack((results.segmentation_mask,) * 3, axis=-1) > 0.5  # 獲取分割條件

        if self.use_bg and self.bg is not None:
            bg_image = cv2.resize(self.bg, (640, 480))  # 調整背景圖像的大小
            output_image = np.where(condition, show_rgb, bg_image)
        else:
            output_image = show_rgb

        showImage = QtGui.QImage(output_image.data, output_image.shape[1], output_image.shape[0], QtGui.QImage.Format_RGB888)  # 把讀取到的視頻數據變成QImage形式
        self.label_show_camera.setPixmap(QtGui.QPixmap.fromImage(showImage))  # 往顯示視頻的Label里顯示QImage

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)  # 固定的，表示程序應用
    ui = Ui_MainWindow()  # 實例化
    ui.show()
    sys.exit(app.exec_())  # 進入程序主循環
