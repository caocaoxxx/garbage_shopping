#include <Servo.h>

Servo servoH; // 水平舵机
Servo servoV; // 垂直舵机

// 引脚定义常量
const int PIN_SERVO_H = 9;      // 水平舵机引脚
const int PIN_SERVO_V = 10;     // 垂直舵机引脚
const int PIN_IR_SENSOR = 4;    // 红外感应器引脚

// 垃圾分类角度映射常量
const int ANGLE_YOUHAI = 270;    // 有害垃圾 270°
const int ANGLE_KEHUISHOU = 180; // 可回收垃圾 180°
const int ANGLE_CHUYU = 90;      // 厨余垃圾 90°
const int ANGLE_QITA = 0;        // 其他垃圾 0°

// 垃圾类型索引常量
const int TYPE_YOUHAI = 0;       // 有害垃圾
const int TYPE_KEHUISHOU = 1;    // 可回收垃圾
const int TYPE_CHUYU = 2;        // 厨余垃圾
const int TYPE_QITA = 3;         // 其他垃圾

// 舵机运动角度常量
const int ANGLE_VERTICAL_DUMP = 45;     // 垂直舵机倾倒角度
const int ANGLE_H_RESET = 0;            // 水平舵机复位角度
const int ANGLE_V_RESET = 15;           // 垂直舵机复位角度

// 时间延迟常量（毫秒）
const unsigned long DELAY_INITIAL = 2000;    // 初始等待时间
const unsigned long DELAY_AFTER_H = 1500;    // 水平舵机转动后等待时间
const unsigned long DELAY_AFTER_V = 1500;    // 垂直舵机转动后等待时间
const unsigned long DELAY_AFTER_V_RESET = 1000; // 垂直舵机复位后等待时间
const unsigned long DELAY_CYCLE = 3000;      // 完成一个周期后等待时间
const unsigned long DELAY_LOOP = 100;        // 主循环延迟时间

// 红外感应相关常量
const unsigned long FULL_DELAY = 3000;       // 满载检测时间阈值(3秒)
const String FULL_PREFIX = "FULL:";          // 满载信号前缀
const String UNFULL_PREFIX = "UNFULL:";      // 解除满载信号前缀

// 红外感应相关变量
unsigned long irTriggeredTime = 0;  // 红外传感器触发时间
bool isFull = false;                // 是否处于满载状态

void setup() {
  Serial.begin(115200);
  
  // 初始化舵机
  servoH.attach(PIN_SERVO_H);
  servoV.attach(PIN_SERVO_V);
  
  // 初始化红外传感器
  pinMode(PIN_IR_SENSOR, INPUT);
  
  // 初始复位位置 - 使用不同的复位角度
  servoH.write(ANGLE_H_RESET);
  servoV.write(ANGLE_V_RESET);
  
  // 初始化完成信息
  Serial.println("垃圾分类系统初始化完成");
}

int mapAngle(int trashType) {
  // 根据垃圾类型索引映射角度
  switch(trashType) {
    case TYPE_YOUHAI:
      return ANGLE_YOUHAI;      // 有害垃圾 270°
    case TYPE_KEHUISHOU:
      return ANGLE_KEHUISHOU;   // 可回收垃圾 180°
    case TYPE_CHUYU:
      return ANGLE_CHUYU;       // 厨余垃圾 90°
    case TYPE_QITA:
      return ANGLE_QITA;        // 其他垃圾 0°
    default:
      return ANGLE_QITA;        // 默认为其他垃圾
  }
}

void checkIRSensor() {
  // 读取红外传感器状态 (HIGH表示检测到物体)
  int irState = digitalRead(PIN_IR_SENSOR);
  
  // 如果检测到物体
  if (irState == HIGH) {
    // 如果是第一次检测到，记录时间
    if (irTriggeredTime == 0) {
      irTriggeredTime = millis();
    } 
    // 如果持续检测到超过阈值时间，且当前非满载状态
    else if (!isFull && (millis() - irTriggeredTime >= FULL_DELAY)) {
      // 发送满载信号 - 默认为可回收垃圾
      Serial.println(FULL_PREFIX + "RECYCLABLE");
      isFull = true;
    }
  } 
  // 如果未检测到物体
  else {
    // 如果之前处于满载状态，发送解除满载信号
    if (isFull) {
      Serial.println(UNFULL_PREFIX + "RECYCLABLE");
      isFull = false;
    }
    // 重置触发时间
    irTriggeredTime = 0;
  }
}

void loop() {
  // 检查红外传感器
  checkIRSensor();
  
  // 处理串口命令
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd.startsWith("CLASS:")) {
      // 解析垃圾类型索引
      int trashType = cmd.substring(6).toInt();
      int targetAngle = mapAngle(trashType);
      
      // 按照新的流程控制舵机运转
      
      // 1. 识别后等待2秒
      delay(DELAY_INITIAL);
      
      // 2. 水平舵机先转动到目标角度
      servoH.write(targetAngle);
      
      // 3. 等待1.5秒
      delay(DELAY_AFTER_H);
      
      // 4. 垂直舵机转动进行倾倒
      servoV.write(ANGLE_VERTICAL_DUMP);
      
      // 5. 等待1.5秒
      delay(DELAY_AFTER_V);
      
      // 6. 垂直舵机回到初始位置
      servoV.write(ANGLE_V_RESET);
      
      // 7. 等待1秒
      delay(DELAY_AFTER_V_RESET);
      
      // 8. 水平舵机回到初始位置
      servoH.write(ANGLE_H_RESET);
      
      // 9. 等待3秒
      delay(DELAY_CYCLE);
      
      // 10. 完成动作后向串口发送确认信息
      Serial.println("DONE");
    }
  }
  
  // 短暂延时，避免过于频繁检测
  delay(DELAY_LOOP);
}
