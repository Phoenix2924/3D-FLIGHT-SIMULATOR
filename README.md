# ESP8266 3D Flight Simulator

A real-time, wireless 3D flight simulator powered by an **ESP8266**, an **MPU6050** accelerometer, **Python**, and **Three.js**. Tilt the hardware controller in your hand to pitch, roll, and bank an aircraft in your web browser with zero external Python dependencies.

---

##  Features

* **Wireless Motion Control:** Uses an ESP8266 in Access Point (AP) mode to stream live pitch and roll telemetry over UDP at ~50Hz.
* **Zero External Python Libraries:** Built entirely with Python's standard library (`socket`, `http.server`, `threading`, `json`).
* **Offline-Ready 3D Graphics:** Automatically caches `three.min.js` (Three.js r128) locally on the first run so you can fly completely offline while connected to the ESP8266 Wi-Fi hotspot.
* **Live Heads-Up Display (HUD):** Displays real-time Pitch, Roll, and Altitude data overlaid on the 3D scene.

---

##  Hardware & Wiring

### Components Needed
* **ESP8266 Board** (NodeMCU, Wemos D1 Mini, etc.)
* **MPU6050** 6-axis Accelerometer/Gyroscope module
* Jumper wires & breadboard

### Pinout Connections

| MPU6050 Pin | ESP8266 (NodeMCU / D1 Mini) |
| :--- | :--- |
| **VCC** | `3V3` |
| **GND** | `GND` |
| **SDA** | `D2` (GPIO 4) |
| **SCL** | `D1` (GPIO 5) |

*(Note: If your MPU6050 `AD0` pin is pulled high to `3V3`, change `MPU_ADDR` in `esp8266_flight_controller.ino` from `0x68` to `0x69`.)*

---

##  Getting Started

### 1. Flash the ESP8266
1. Open `esp8266_flight_controller.ino` in the Arduino IDE.
2. Set your desired `AP_SSID` and `AP_PASS` (minimum 8 characters).
3. Ensure you have the **ESP8266 Board Package** installed (no external sensor libraries are required—it uses the built-in `Wire` library).
4. Upload the code to your ESP8266.

### 2. Run the Python Server
1. First, run the script once while connected to the internet so it can download and cache `three.min.js` (or keep `three.min.js` in the same folder as `flight.py`):
   ```bash
   python flight.py
   ```
2. Connect your computer to the Wi-Fi hotspot broadcast by your ESP8266.
3. With `flight.py` running, open your browser and navigate to **`http://localhost:8000`**.

---

##  How It Works

1. **Sensor Fusion & Transmission (C++ / ESP8266):** The ESP8266 reads raw X, Y, and Z accelerometer values over I2C, calculates pitch and roll angles in degrees, and broadcasts them as comma-separated UDP packets (`"pitch,roll"`) on port `4210`.
2. **Backend Bridge (Python):** A background thread listens for incoming UDP packets on port `4210` while a lightweight HTTP server serves the web interface and exposes a `/data` JSON endpoint.
3. **3D Rendering (Three.js):** The browser polls `/data` every 30ms to update the 3D aircraft's orientation, turning rate (yaw from banking), forward motion, and smooth chase camera.

---
## Circuit Diagram 
   +-----------------------+             +-----------------------+

   |   ESP8266 (NodeMCU)   |             |        MPU6050        |
   |                       |             |                       |
   |                  3V3  |------------>| VCC                   |
   |                  GND  |------------>| GND                   |
   |          D2 (GPIO 4)  |------------>| SDA                   |
   |          D1 (GPIO 5)  |------------>| SCL                   |
   +-----------------------+             +-----------------------+
---
##  Project Structure

```text
├── esp8266_flight_controller.ino   # ESP8266 firmware for reading MPU6050 & broadcasting UDP
├── flight.py                       # Python UDP listener, HTTP server & embedded Three.js frontend
├── .gitignore                      # Ignores local cache, build artifacts, and downloaded JS
└── LICENSE                         # MIT License
```

