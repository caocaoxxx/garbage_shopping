from ultralytics import YOLO
import os
import time

def export_model_to_onnx():
    try:
        print("开始导出ONNX模型...")
        
        # 检查PT模型是否存在
        if not os.path.exists("best.pt"):
            print("错误：best.pt模型文件不存在！")
            return False
            
        # 加载PyTorch模型
        print("加载PyTorch模型...")
        model = YOLO("best.pt")
        
        # 使用简化参数导出ONNX
        print("正在导出为ONNX格式(opset=9)...")
        start_time = time.time()
        
        # 简化导出命令
        model.export(format="onnx", opset=9)
        
        # 检查导出结果
        if os.path.exists("best.onnx"):
            elapsed_time = time.time() - start_time
            file_size = os.path.getsize("best.onnx") / (1024 * 1024)
            print(f"ONNX模型导出成功! 耗时: {elapsed_time:.2f}秒, 文件大小: {file_size:.2f} MB")
            return True
        else:
            print("导出失败：未找到生成的ONNX文件")
            return False
            
    except Exception as e:
        print(f"发生异常: {e}")
        return False

if __name__ == "__main__":
    export_model_to_onnx()