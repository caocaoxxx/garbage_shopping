#include <Servo.h>

Servo servoH; // 水平舵机
Servo servoV; // 垂直舵机

const int pinH = 9;
const int pinV = 10;
const int irSensorPin = 4;  // 红外感应器连接到4号引脚

// 垃圾分类角度映射
const int ANGLE_YOUHAI = 270;    // 有害垃圾 270°
const int ANGLE_KEHUISHOU = 180; // 可回收垃圾 180°
const int ANGLE_CHUYU = 90;      // 厨余垃圾 90°
const int ANGLE_QITA = 0;        // 其他垃圾 0°

// 红外感应相关变量
unsigned long irTriggeredTime = 0;  // 红外传感器触发时间
bool isFull = false;  // 是否处于满载状态
const unsigned long FULL_DELAY = 3000;  // 满载检测时间阈值(3秒)

void setup() {
  Serial.begin(115200);
  
  // 初始化舵机
  servoH.attach(pinH);
  servoV.attach(pinV);
  
  // 初始化红外传感器
  pinMode(irSensorPin, INPUT);
  
  // 初始复位位置
  servoH.write(0);
  servoV.write(0);
  
  // 初始化完成信息
  Serial.println("垃圾分类系统初始化完成");
}

int mapAngle(String cls) {
  // 根据分类映射角度
  if (cls == "QITA") return ANGLE_QITA;        // 其他垃圾 0°
  else if (cls == "CHUYU") return ANGLE_CHUYU;  // 厨余垃圾 90°
  else if (cls == "KEHUISHOU") return ANGLE_KEHUISHOU; // 可回收垃圾 180°
  else if (cls == "YOUHAI") return ANGLE_YOUHAI;   // 有害垃圾 270°
  else return ANGLE_QITA; // 默认为其他垃圾
}

void checkIRSensor() {
  // 读取红外传感器状态 (HIGH表示检测到物体)
  int irState = digitalRead(irSensorPin);
  
  // 如果检测到物体
  if (irState == HIGH) {
    // 如果是第一次检测到，记录时间
    if (irTriggeredTime == 0) {
      irTriggeredTime = millis();
    } 
    // 如果持续检测到超过阈值时间，且当前非满载状态
    else if (!isFull && (millis() - irTriggeredTime >= FULL_DELAY)) {
      // 发送满载信号 - 默认为可回收垃圾
      Serial.println("FULL:RECYCLABLE");
      isFull = true;
    }
  } 
  // 如果未检测到物体
  else {
    // 如果之前处于满载状态，发送解除满载信号
    if (isFull) {
      Serial.println("UNFULL:RECYCLABLE");
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
      String cls = cmd.substring(6);
      int targetAngle = mapAngle(cls);
      // 水平→垂直→复位控制序列
      // 水平舵机动作
      servoH.write(targetAngle);
      delay(2000);
      // 垂直舵机动作
      servoV.write(90); // 垂直舵机只需要90度动作
      delay(2000);
      // 复位：垂直舵机先复位
      servoV.write(0);
      delay(1000);
      servoH.write(0);
      delay(1000);
      // 完成动作后向串口发送确认信息
      Serial.println("DONE");
    }
  }
  
  // 短暂延时，避免过于频繁检测
  delay(100);
}
