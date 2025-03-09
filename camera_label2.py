from ultralytics import YOLO
import cv2
import time

# 加载训练好的模型
model = YOLO('best.onnx')  # 替换为你的模型路径

# 获取类别名称列表
class_names = model.names

# 打开摄像头
cap = cv2.VideoCapture(0)  # 0 表示默认摄像头

# 初始化FPS计时器
time_last = time.time()   # 上一次计时时间
frame_count = 0          # 帧计数器

while True:
    # 读取摄像头帧
    ret, frame = cap.read()
    if not ret:
        break

    # 使用模型进行预测
    results = model.predict(
        source=frame,  # 直接传入帧图像
        conf=0.8,  # 置信度阈值
        iou=0.45,  # IoU 阈值
        device=0  # 使用 CPU
    )

    # 解析预测结果并绘制标签名称
    for result in results:
        boxes = result.boxes
        for box in boxes:
            # 获取边界框坐标
            x1, y1, x2, y2 = map(int, box.xyxy[0])  # 边界框坐标
            # 获取类别索引并映射为类别名称
            class_index = int(box.cls)
            class_name = class_names[class_index]
            # 获取置信度
            confidence = float(box.conf)
            # 在图像上绘制标签名称和置信度
            label = f"{class_name} {confidence:.2f}"
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)  # 绘制边界框
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)  # 绘制标签

    # 计算并显示帧率（FPS）
    current_time = time.time()
    delta_time = current_time - time_last

    # 每秒更新一次FPS
    if delta_time >= 1:
        fps = frame_count / delta_time
        time_last = current_time
        frame_count = 0
    frame_count += 1

    # 在画面左上角显示FPS
    cv2.putText(frame, f"FPS: {fps:.1f}", (10, 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # 将帧调整为原来的两倍大小用于显示
    display_frame = cv2.resize(frame, (frame.shape[1] * 2, frame.shape[0] * 2))

    # 显示帧
    cv2.imshow("Camera Prediction", display_frame)

    # 按下 'q' 键退出
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 释放摄像头并关闭窗口
cap.release()
cv2.destroyAllWindows()