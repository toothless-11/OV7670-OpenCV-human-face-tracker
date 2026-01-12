


// change setup.h to switch between buffered and pixel-by-pixel processing
#include "setup.h"


// 定义电机4个控制引脚
int IN1 = 8;
int IN2 = 9;
int IN3 = 10;
int IN4 = 11;

//引用外部文件定义的变量
extern int motorDir;
extern int stepIndex;



void setup() {
  // This is not necessary and has no effect for ATMEGA based Arduinos.
  // WAVGAT Nano has slower clock rate by default. We want to reset it to maximum speed
  CLKPR = 0x80; // enter clock rate change mode
  CLKPR = 0; // set prescaler to 0. WAVGAT MCU has it 3 by default.
  
  //电机控制引脚
  DDRB |= 0b00001111;   // PB0~PB3 设为输出
  initializeScreenAndCamera();
}

void loop() {

  if (Serial.available()) {
    int c = Serial.read();

    if (c == 100)      motorDir = 1;    // 顺时针
    else if (c == 99)  motorDir = -1;   // 逆时针
  }
  else               motorDir = 0;    // 停
  
  
  processFrame();   // 相机采集，爱卡多久卡多久
}
