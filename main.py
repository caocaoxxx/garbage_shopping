import sys, cv2, time, threading, queue
import serial
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QWidget, QTextEdit, 
                            QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, 
                            QHeaderView, QSizePolicy)
from PyQt5.QtCore import QTimer, Qt, QSize, QMetaObject, pyqtSlot
from PyQt5.QtGui import QImage, QPixmap, QFont
# 假设已安装 ultralytics
from ultralytics import YOLO
# 添加PIL相关导入，用于中文显示
from PIL import ImageFont, ImageDraw, Image
import numpy as np

# 修改为新的分类标签映射
ANGLE_MAPPING = {
    'qita': 0,      # 其他垃圾
    'chuyu': 90,    # 厨余垃圾
    'kehuishou': 180,  # 可回收物
    'youhai': 270   # 有害垃圾
}

# 中文名称映射
CLASS_NAMES_CN = {
    'qita': '其他垃圾',
    'chuyu': '厨余垃圾',
    'kehuishou': '可回收垃圾',  # 修正为可回收物
    'youhai': '有害垃圾'
}

# 垃圾类型枚举
class TrashType:
    YOUHAI = 0      # 有害垃圾
    KEHUISHOU = 1   # 可回收垃圾
    CHUYU = 2       # 厨余垃圾
    QITA = 3        # 其他垃圾

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("生活垃圾智能分类系统")
        self.setMinimumSize(1200, 900)  # 调整窗口尺寸
        
        # 新增顶部标题标签，并增大字号
        headerLabel = QLabel("生活垃圾智能分类系统")
        headerLabel.setAlignment(Qt.AlignCenter)
        headerLabel.setFont(QFont("Arial", 24, QFont.Bold))  # 增大字号
        headerLabel.setStyleSheet("margin: 10px;")  # 增加边距
        
        # 初始化各窗口部件
        self.videoLabel = QLabel()
        self.videoLabel.setMinimumSize(450, 350)  # 增大视频显示区域
        self.videoLabel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.videoLabel.setAlignment(Qt.AlignCenter)
        self.videoLabel.setStyleSheet("border: 1px solid #cccccc; background-color: #f0f0f0;")
        
        self.movieLabel = QLabel()
        self.movieLabel.setMinimumSize(450, 350)  # 增大视频显示区域
        self.movieLabel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.movieLabel.setAlignment(Qt.AlignCenter)
        self.movieLabel.setStyleSheet("border: 1px solid #cccccc; background-color: #f0f0f0;")
        
        # 状态表格 - 修改回4行
        self.statusTable = QTableWidget(4, 4)
        self.statusTable.setHorizontalHeaderLabels(["序号", "垃圾类型", "数量", "状态"])
        self.statusTable.setStyleSheet("QHeaderView::section { background-color: #e1e1e1; }")
        
        # 固定表格大小并调整列宽度比例
        self.statusTable.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.statusTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.statusTable.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.statusTable.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        
        # 设置列宽
        self.statusTable.setColumnWidth(0, 60)
        self.statusTable.setColumnWidth(2, 80)
        self.statusTable.setColumnWidth(3, 120)
        
        # 禁用水平滚动条
        self.statusTable.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # 根据4行内容调整固定高度
        self.statusTable.setMinimumHeight(180)  # 增加表格高度以容纳4行
        self.statusTable.setMaximumHeight(180)
        
        # 日志区域
        self.logArea = QTextEdit()
        self.logArea.setMinimumHeight(150)
        self.logArea.setStyleSheet("border: 1px solid #cccccc; background-color: #f8f8f8;")
        self.logArea.setReadOnly(True)
        
        # 不再需要单独的视频标题标签，删除这些代码
        
        # 只保留状态表格和日志区域的标题标签
        statusTitleLabel = QLabel("垃圾分类状态")
        statusTitleLabel.setAlignment(Qt.AlignCenter)
        statusTitleLabel.setFont(QFont("Arial", 12, QFont.Bold))
        
        logTitleLabel = QLabel("系统日志显示")
        logTitleLabel.setAlignment(Qt.AlignCenter)
        logTitleLabel.setFont(QFont("Arial", 12, QFont.Bold))
        
        # 初始化垃圾计数和状态 - 增加状态跟踪
        self.counts = {cls: 0 for cls in CLASS_NAMES_CN.values()}
        self.states = {cls: "待检测" for cls in CLASS_NAMES_CN.values()}
        
        # 默认将可回收垃圾状态设为"待检测"
        self.states["可回收垃圾"] = "待检测"
        
        # 满载状态监测变量
        self.full_status = {cls: False for cls in CLASS_NAMES_CN.values()}
        
        self.updateStatusTable()

        # 帧率计算相关变量
        self.prev_frame_time = 0
        self.new_frame_time = 0
        self.fps = 0

        # 视频区布局 - 去掉标题，直接添加视频标签
        videoLayout = QVBoxLayout()
        videoLayout.addWidget(self.videoLabel)
        
        movieLayout = QVBoxLayout()
        movieLayout.addWidget(self.movieLabel)
        
        hlayoutVideos = QHBoxLayout()
        hlayoutVideos.addLayout(movieLayout)
        hlayoutVideos.addLayout(videoLayout)
        
        # 状态表格布局
        statusLayout = QVBoxLayout()
        statusLayout.addWidget(statusTitleLabel)
        statusLayout.addWidget(self.statusTable)
        
        # 系统日志布局
        logLayout = QVBoxLayout()
        logLayout.addWidget(logTitleLabel)
        logLayout.addWidget(self.logArea)
        
        # 整体垂直布局：标题 - 视频区 - 状态表格 - 日志区
        vlayout = QVBoxLayout()
        vlayout.addWidget(headerLabel)  # 顶部标题
        vlayout.addLayout(hlayoutVideos, 3)  # 视频区占较大比重
        vlayout.addLayout(statusLayout, 1)
        vlayout.addLayout(logLayout, 1)
        
        centralWidget = QWidget()
        centralWidget.setLayout(vlayout)
        self.setCentralWidget(centralWidget)

        # 设置表格所在布局的最小宽度
        statusLayout.setContentsMargins(10, 5, 10, 5)  # 增加左右间距

        # 视频文件和摄像头初始化
        self.movieCap = cv2.VideoCapture("movie.mp4")
        self.detCap = cv2.VideoCapture(1)  # 使用外接摄像头(索引为1)

        # 加载YOLOv8模型(best.pt)
        self.model = YOLO("best.pt")

        # 串口初始化（COM4，115200）
        try:
            self.ser = serial.Serial("COM4", 115200, timeout=1)
        except Exception as e:
            self.log("串口异常：" + str(e))
            self.ser = None

        # 互斥锁（用作舵机动作期间锁定检测）
        self.servo_lock = threading.Lock()

        # 定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.updateFrames)
        self.timer.start(30)

        # 添加检测计数器和处理标志
        self.detection_count = 1
        self.can_process = True
        
        # 当前正在处理的垃圾项
        self.processing_item = None
        
        # 加载中文字体用于显示检测框标签
        try:
            self.font = ImageFont.truetype('SimHei.ttf', 20)
            self.log("成功加载中文字体")
        except Exception as e:
            self.log(f"加载中文字体失败: {str(e)}")
            self.font = None
        
    def updateStatusTable(self):
        # 更新状态表格，包含新的状态显示逻辑
        items = list(self.counts.items())
        
        for row, (cls, count) in enumerate(items):
            # 序号列
            item0 = QTableWidgetItem(str(row+1))
            item0.setTextAlignment(Qt.AlignCenter)
            self.statusTable.setItem(row, 0, item0)
            
            # 类型列
            item1 = QTableWidgetItem(cls)
            item1.setTextAlignment(Qt.AlignCenter)
            self.statusTable.setItem(row, 1, item1)
            
            # 数量列
            item2 = QTableWidgetItem(str(count))
            item2.setTextAlignment(Qt.AlignCenter)
            self.statusTable.setItem(row, 2, item2)
            
            # 状态列 - 根据状态跟踪变量显示
            status = self.states[cls]
            
            # 如果是满载状态，优先显示满载
            if self.full_status[cls]:
                status = "满载"
            
            item3 = QTableWidgetItem(status)
            item3.setTextAlignment(Qt.AlignCenter)
            
            # 根据状态设置不同颜色
            if status == "满载":
                item3.setBackground(Qt.red)
                item3.setForeground(Qt.white)
            elif status == "检测中":
                item3.setBackground(Qt.yellow)
            elif status == "分类完成":
                item3.setBackground(Qt.green)
            
            self.statusTable.setItem(row, 3, item3)
        
        # 确保表格更新后能显示全部内容
        self.statusTable.resizeRowsToContents()

    def updateFrames(self):
        # 更新movie视频帧
        ret, frame = self.movieCap.read()
        if not ret:
            self.movieCap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.movieCap.read()
        self.displayFrame(frame, self.movieLabel)
        
        # 更新实时检测视频帧 - 始终显示检测框，即使在处理垃圾期间
        ret, frame2 = self.detCap.read()
        if ret:
            # 运行YOLOv8检测 - 不再受舵机锁和处理项状态限制
            results = self.model(frame2, verbose=False)  # 关闭详细输出提高性能
            
            # 计算帧率
            self.new_frame_time = time.time()
            fps = 1 / (self.new_frame_time - self.prev_frame_time) if self.prev_frame_time > 0 else 0
            self.prev_frame_time = self.new_frame_time
            # 平滑帧率显示
            self.fps = 0.9 * self.fps + 0.1 * fps if self.fps > 0 else fps
            
            # 在图像左上角添加帧率文本，使用中文显示
            fps_text = f"帧率: {int(self.fps)}"
            frame2 = self.draw_chinese_text(frame2, fps_text, (10, 10), text_color=(0, 255, 0))
            
            # 遍历检测结果并在图像上绘制 - 始终执行这部分，确保检测框显示
            if len(results) > 0:
                result = results[0]
                boxes = result.boxes
                
                # 检查是否有检测结果
                if len(boxes) > 0:
                    # 获取最大置信度的检测结果
                    confidence = boxes.conf.max().item()
                    if confidence > 0.5:  # 设置置信度阈值
                        # 获取最大置信度对应的索引
                        max_index = boxes.conf.argmax().item()
                        box = boxes.xyxy[max_index].cpu().numpy().astype(int)
                        cls = int(boxes.cls[max_index].item())
                        
                        # 获取对应的标签和中文名称
                        label_keys = list(CLASS_NAMES_CN.keys())
                        if cls < len(label_keys):
                            label_key = label_keys[cls]
                            label_cn = CLASS_NAMES_CN[label_key]
                            
                            # 在检测框上绘制边界框
                            x1, y1, x2, y2 = box
                            cv2.rectangle(frame2, (x1, y1), (x2, y2), (0, 255, 0), 2)
                            
                            # 绘制带有置信度的中文标签
                            label_text = f"{label_cn}: {confidence:.2f}"
                            # 在框上方绘制带背景的中文标签
                            frame2 = self.draw_chinese_text(
                                frame2, 
                                label_text, 
                                (x1, y1-25), 
                                text_color=(0, 0, 0),
                                bg_color=(0, 255, 0)
                            )
                            
                            # 仅在满足条件时触发处理事件（与显示检测框分离）
                            if hasattr(self, 'can_process') and self.can_process and not self.servo_lock.locked() and self.processing_item is None:
                                # 创建一个新线程处理检测结果，避免阻塞UI
                                process_thread = threading.Thread(
                                    target=self.processDetection, 
                                    args=(label_key, label_cn, self.detection_count),
                                    daemon=True
                                )
                                process_thread.start()
                                self.can_process = False  # 禁止下一次处理，直到当前处理完成
                                self.detection_count += 1

            # 无论是否检测或处理，都显示当前帧
            self.displayFrame(frame2, self.videoLabel)

    def displayFrame(self, frame, label):
        # 统一处理视频帧显示，不再区分movieLabel和videoLabel
        rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgbImage.shape
        bytesPerLine = ch * w
        convertToQtFormat = QImage(rgbImage.data, w, h, bytesPerLine, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(convertToQtFormat)
        # 调整图像大小使其适应标签但保持纵横比
        label_size = label.size()
        scaled_pixmap = pixmap.scaled(label_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        label.setPixmap(scaled_pixmap)
        # 居中显示
        label.setAlignment(Qt.AlignCenter)

    def log(self, message):
        # 添加时间戳
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        formatted_message = f"[{timestamp}] {message}"
        self.logArea.append(formatted_message)
        # 自动滚动到底部
        self.logArea.verticalScrollBar().setValue(self.logArea.verticalScrollBar().maximum())

    def reset_process_flag(self):
        """定期重置处理标志，允许进行新的检测"""
        if not self.servo_lock.locked():
            self.can_process = True

    def processDetection(self, label_key, label_cn, index):
        """处理检测到的垃圾分类"""
        try:
            # 设置当前正在处理的垃圾项，防止重复识别
            self.processing_item = label_key
            
            # 修改：先记录当前数量，确保日志与表格显示一致
            current_count = self.counts[label_cn]
            
            # 更新状态为"检测中"
            self.states[label_cn] = "检测中"
            QMetaObject.invokeMethod(self, "updateTableSafe", Qt.QueuedConnection)
            
            # 修改：使用正确的当前数量进行日志记录
            self.log(f"检测到第{index}个物体: {label_cn}, 当前数量: {current_count}")
            print(f"检测到第{index}个物体: {label_cn}, 当前数量: {current_count}")  # 同时输出到终端
            
            # 锁定检测期间，发送舵机控制指令
            self.servo_lock.acquire()
            if self.ser:
                try:
                    # 使用更新后的垃圾类型标签
                    cmd = f"CLASS:{label_key.upper()}"
                    self.ser.write(cmd.encode())
                    print(f"发送指令: {cmd}")  # 输出到终端
                except Exception as e:
                    error_msg = f"串口写入异常：{str(e)}"
                    self.log(error_msg)
                    print(error_msg)  # 输出到终端
            
            # 等待Arduino完成动作，可能会收到DONE信号或者设定超时时间
            # 这里我们继续使用6秒的等待，确保舵机动作完成并复位
            time.sleep(6)
            
            # 更新计数，先更新内部记录后在界面上显示（舵机必须完全复位后才能更新数量显示）
            self.counts[label_cn] += 1
            
            # 记录更新后的数量
            update_msg = f"垃圾投放完成: {label_cn}, 更新数量: {self.counts[label_cn]}"
            self.log(update_msg)
            print(update_msg)  # 输出到终端
            
            # 更新状态为"分类完成"
            self.states[label_cn] = "分类完成"
            
            # 使用QMetaObject.invokeMethod来确保在主线程中更新UI
            QMetaObject.invokeMethod(self, "updateTableSafe", Qt.QueuedConnection)
            
            self.servo_lock.release()
            
            # 设置一个延时器，在3秒后将状态恢复为"待检测"
            # 除非是满载状态，满载状态优先级更高
            QTimer.singleShot(3000, lambda cn=label_cn: self.resetStateForItem(cn))
            
            # 重置处理标志，允许处理下一个检测
            self.can_process = True
            
        except Exception as e:
            error_msg = f"处理检测时出错: {str(e)}"
            print(error_msg)  # 输出到终端
            self.log(error_msg)
            if self.servo_lock.locked():
                self.servo_lock.release()
            self.can_process = True
        finally:
            # 在处理完成后（无论成功还是失败）重置处理项
            self.processing_item = None

    @pyqtSlot()
    def updateTableSafe(self):
        """安全地在主线程中更新表格"""
        self.updateStatusTable()

    def resetStateForItem(self, label_cn):
        """在3秒后将特定垃圾项的状态重置为待检测"""
        if not self.full_status[label_cn]:  # 只有在非满载状态下才重置状态
            self.states[label_cn] = "待检测"
            QMetaObject.invokeMethod(self, "updateTableSafe", Qt.QueuedConnection)
            print(f"{label_cn}状态重置为待检测")

    def read_serial(self):
        """监听串口，接收来自Arduino的满载信号"""
        while True:
            if self.ser and self.ser.is_open:
                try:
                    if self.ser.in_waiting:
                        line = self.ser.readline().decode('utf-8').strip()
                        if line.startswith("FULL:"):
                            trash_type = line.split(":")[1]
                            self.handle_full_signal(trash_type, True)
                        elif line.startswith("UNFULL:"):
                            trash_type = line.split(":")[1]
                            self.handle_full_signal(trash_type, False)
                        elif line == "DONE":
                            # 舵机动作完成信号，可以在这里添加处理逻辑
                            print("收到舵机动作完成信号")
                except Exception as e:
                    print(f"串口读取出错: {str(e)}")
            time.sleep(0.1)
    
    def handle_full_signal(self, trash_type, is_full):
        """处理满载/不满载信号"""
        if trash_type == "RECYCLABLE":
            cn_type = "可回收垃圾"
        elif trash_type == "HAZARDOUS":
            cn_type = "有害垃圾"
        elif trash_type == "KITCHEN":
            cn_type = "厨余垃圾"
        elif trash_type == "OTHER":
            cn_type = "其他垃圾"
        else:
            return
        
        if is_full:
            msg = f"{cn_type}已满载！"
            self.log(msg)
            print(msg)
            self.full_status[cn_type] = True
        else:
            msg = f"{cn_type}已恢复正常"
            self.log(msg)
            print(msg)
            self.full_status[cn_type] = False
            self.states[cn_type] = "待检测"
        
        # 更新UI
        QMetaObject.invokeMethod(self, "updateTableSafe", Qt.QueuedConnection)

    def draw_chinese_text(self, frame, text, position, text_color=(0, 255, 0), bg_color=None):
        """使用PIL绘制中文文本到图像上"""
        if self.font is None:
            # 如果字体未加载，使用默认方式显示（可能会有乱码）
            cv2.putText(frame, text, position, cv2.FONT_HERSHEY_SIMPLEX, 0.8, text_color, 2)
            return frame
        
        # 转换图像格式用于PIL处理
        img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)
        
        # 如果需要背景色
        if bg_color is not None:
            # 计算文本区域大小
            text_size = draw.textbbox((0, 0), text, font=self.font)[2:]
            # 绘制背景矩形
            draw.rectangle(
                [position[0], position[1], position[0] + text_size[0], position[1] + text_size[1]],
                fill=bg_color
            )
        
        # 绘制文本
        draw.text(position, text, font=self.font, fill=text_color)
        
        # 转换回OpenCV格式
        return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())