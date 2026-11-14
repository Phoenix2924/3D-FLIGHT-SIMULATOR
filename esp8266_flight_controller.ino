// ESP8266 + MPU6050 flight controller for flight_sim.py
// Wiring (NodeMCU / Wemos D1 mini):
//   MPU6050 VCC -> 3V3
//   MPU6050 GND -> GND
//   MPU6050 SDA -> D2 (GPIO4)
//   MPU6050 SCL -> D1 (GPIO5)
// No extra libraries needed (uses Wire directly).

#include <ESP8266WiFi.h>
#include <WiFiUdp.h>
#include <Wire.h>

const char* AP_SSID = "ESP-FlightSim";   // change to your network name
const char* AP_PASS = "12345678";        // at least 8 characters

IPAddress broadcastIP(192, 168, 4, 255);
const unsigned int UDP_PORT = 4210;

const uint8_t MPU_ADDR = 0x68;           // use 0x69 if AD0 pin is tied to 3V3

WiFiUDP udp;

bool readMPU(float &pitch, float &roll) {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x3B);                      // ACCEL_XOUT_H
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom((int)MPU_ADDR, 6, (int)true) != 6) return false;

  int16_t ax = (Wire.read() << 8) | Wire.read();
  int16_t ay = (Wire.read() << 8) | Wire.read();
  int16_t az = (Wire.read() << 8) | Wire.read();

  float fx = ax / 16384.0;
  float fy = ay / 16384.0;
  float fz = az / 16384.0;

  pitch = atan2(-fx, sqrt(fy * fy + fz * fz)) * 180.0 / PI;
  roll  = atan2(fy, fz) * 180.0 / PI;
  return true;
}

void setup() {
  Serial.begin(115200);
  delay(200);
  Serial.println();

  Wire.begin(4, 5);                      // SDA = GPIO4 (D2), SCL = GPIO5 (D1)


  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x6B);
  Wire.write(0x00);
  byte err = Wire.endTransmission();
  if (err == 0) {
    Serial.println("MPU6050 found and awake.");
  } else {
    Serial.print("MPU6050 NOT found, I2C error ");
    Serial.println(err);
    Serial.println("Check wiring (SDA->D2, SCL->D1, 3V3, GND) and address (0x68/0x69).");
  }

  // ESP8266 creates its own Wi-Fi network
  WiFi.mode(WIFI_AP);
  WiFi.softAP(AP_SSID, AP_PASS);
  Serial.print("Access point started. ESP IP: ");
  Serial.println(WiFi.softAPIP());
}

void loop() {
  float pitch, roll;
  if (readMPU(pitch, roll)) {
    char msg[32];
    snprintf(msg, sizeof(msg), "%.1f,%.1f", pitch, roll);
    udp.beginPacket(broadcastIP, UDP_PORT);
    udp.write((const uint8_t*)msg, strlen(msg));
    udp.endPacket();
    Serial.println(msg);                 // watch this in Serial Monitor
  } else {
    Serial.println("MPU6050 read failed");
  }
  delay(20);
}
