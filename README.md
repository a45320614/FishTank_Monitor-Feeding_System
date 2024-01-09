# 物聯網期末專案 - 魚缸監測餵食系統

![171728](https://github.com/a45320614/FishTank_Monitor-Feeding_System/assets/92359154/46180c2a-38f1-4c62-b8c2-cb22a3a83948)

## 1. Introduction
* This project aims to help those who need a monitor system for their fish tank when they are out for a long time. compared to the "Smart fish tank" on the market, we have the advantage that we can see our precious little guys swimming via any device, and feeding,  is also included, no matter where you are.

## 2. Demo video
* Briefly shows how the system works.
* Click the image below to watch the video on YouTube.

[![Demo影片](https://img.youtube.com/vi/EiCibyWQGEY/0.jpg)](https://youtu.be/EiCibyWQGEY)

## 3. Requirement
### 3.1 Components
#### 1. Raspberry Pi 4B * 1
- We build and run our project on Raspberry Pi.
#### 3. Breadboard (Full-sized)
#### 4. Sensors
- To achieve the goal of making a monitor system, we need some sensors, without them, we couldn't get any data we want.
1. DFRobot SEN0161 Gravity: Analog pH Sensor
2. Grove TDS sensor * 1
3. DS18B20 Water temperature sensor * 1
4. US-100 ultrasonic sensor * 1
#### 5. MCP3008
- Some of the sensors are analog output, Raspberry Pi can only read digital data, so we need an Analog-to-Digital Converter (ADC).
#### 6. Motors 
- We also need different types of motors.
1. 385 DC motor * 2
2. sg90 servo motor * 1
#### 7. 1-channel relay * 2
- You can also use the L298N motor driver to control the DC motor.
#### 8. Raspberry Pi camera module * 1
#### 9. Battery holder * 1 and AA battery * 4
- Power supply for 385 motor.
#### 10. PVC hose * 4 (inside diameter 6, outside diameter 8.5)
#### 11. Fish tank * 1
#### 12. Container for water * 2
#### 13. A huge amount of jump wire is needed, make sure you prepare a bunch of them.

### 3.2 Environment 
- Python 3.7 is used in this project.
#### 3.2.1 Installation
- Enter the commands below in your Raspberry Pi terminal.
1. RPi.GPIO
	- For getting the data from Raspberry Pi pin.
	```shell=
	$ pip install RPi.GPIO
	```
2. Spidev
	- For ADC.
	```
	$ pip install spidev
	```
3. Flask
	- For web framework.
	```
	$ pip install flask
	```
4. mjpg-streamer
	- For streaming.
  ```
	$ sudo apt-get install libjpeg8-dev
	$ sudo apt-get install imagemagick
	$ git clone https://github.com/jacksonliam/mjpg-streamer.git 
	$ cd mjpg-streamer/mjpg-streamer-experimental 
	$ make
  ```
  * If you run into the error below, install "cmake".
  ```
  [ -d _build ] || mkdir _build 
  [ -f _build/Makefile ] || (cd _build && cmake -DCMAKE_BUILD_TYPE=Release ..) 
  /bin/sh: 1: cmake: not found 
  make: *** [Makefile:18: all] Error 127
  ```

  ```
  sudo apt-get install cmake
  ```
#### 3.2.2 Raspberry Pi setting
1. Enable SPI interface & Camera
  ```
	$ sudo raspi-config
  ```
1. Select Interfacing Options
   
![Pasted image 20240109033323](https://github.com/a45320614/FishTank_Monitor-Feeding_System/assets/92359154/2ac296ce-65a9-48bc-a403-2a53eac88239)

2. Select SPI and choose yes

![Pasted image 20240109033334](https://github.com/a45320614/FishTank_Monitor-Feeding_System/assets/92359154/ad56a66d-29fd-4e3f-8e0e-fb8184a84a4f)

3. Select Camera and choose yes

![Pasted image 20240109033710](https://github.com/a45320614/FishTank_Monitor-Feeding_System/assets/92359154/ee3f6a1b-90b8-4c3f-9479-f9f172cec4cf)


### 3.3 Not required but helpful
- Use Local VSCode for development, you can also see the detailed tutorial [here](https://randomnerdtutorials.com/raspberry-pi-remote-ssh-vs-code/).
1. Install the extension "Remote - SSH" in your local VSCode
  
![Pasted image 20240109035843](https://github.com/a45320614/FishTank_Monitor-Feeding_System/assets/92359154/9ae098e6-e5ef-43b2-a59c-ebc9ed465b07)

2. Click the Remote - SSH button on the left sidebar.
 
![Pasted image 20240109040008](https://github.com/a45320614/FishTank_Monitor-Feeding_System/assets/92359154/8070dc8d-81e0-44f5-820e-8592a539a7fa)

3. Click "New Remote", the plus sign.
 
![Pasted image 20240109040057](https://github.com/a45320614/FishTank_Monitor-Feeding_System/assets/92359154/f99f34ab-c938-4c87-bcea-b5786eff1c5b)

4. Enter your username and Raspberry Pi ip address.
 
![Pasted image 20240109040304](https://github.com/a45320614/FishTank_Monitor-Feeding_System/assets/92359154/f2bef3ad-bb7b-4526-9fdd-5d9074eaab46)

	 
## 4. Instructions
### 1.MCP3008
- For analog pH sensor and analog TDS sensor.

![image](https://github.com/a45320614/FishTank_Monitor-Feeding_System/assets/92359154/8112ebfa-d017-4692-8dc1-d1d24c77b8f2)

1. Plug MCP3008 into the center of the breadboard.
2. Connect MCP3008 to Raspberry Pi like this.
- Left side is MCP3008 pin.
- Right side is Raspberry Pi pin.
- NOTICE: The voltage for MCP3008 can either be 3.3V or 5V. I use 5V for higher sensitivity.

![image](https://github.com/a45320614/FishTank_Monitor-Feeding_System/assets/92359154/0334405a-7912-4a7c-a8b3-c6b97eeb5fd6)

![image](https://github.com/a45320614/FishTank_Monitor-Feeding_System/assets/92359154/1a90dff2-228a-487a-b8f2-177cd0186805)

Code:
```python
# Reference: https://s761111.gitbook.io/raspi-sensor/pai-bi-wei-li
import spidev

spi = spidev.SpiDev()
spi.open(0,0)
spi.max_speed_hz = 1350000

def ReadADC(channel):
    try:
        if ((channel > 7) or (channel < 0)):
            return "Channel錯誤!"
        adc = spi.xfer2([1,(8+channel)<<4,0])
        adc_value = ((adc[1]&3)<<8) + adc[2]
        return adc_value
    except Exception as e:
        print("無法讀取ADC: {}".format(e))
```
### 2. pH sensor
#### 1. Connect pH sensor to breadboard.
1. VCC -> 5v
2. GND -> GND
3. Signal -> MCP3008 channel (pick the channel you like)
#### 2. pH Calibration
1. Code:
  ```python
   # Reference: https://github.com/DFRobot/DFRobot_PH/tree/master/python/raspberrypi
   import time

   ph_ch = YOUR_CHANNEL

   _acidVoltage = YOUR_VALUE
   _neutralVoltage = YOUR_VALUE
  
  def ph():
    try:
        time.sleep(0.1) 
        adc_value=ReadADC(ph_ch)
        voltage = float(adc_value) * 5
        print("pH sensor的電壓為: " + str(voltage))

        if voltage == 0:
            print("電壓為0，無法讀取pH值")
            return 0

        slope = (7.0-4.0)/((_neutralVoltage-1500.0)/3.0 - (_acidVoltage-1500.0)/3.0)
        intercept = 7.0 - slope*(_neutralVoltage-1500.0)/3.0
        ph_value  = slope*(voltage-1500.0)/3.0+intercept
        print("PH value: "+str(ph_value))
        return round(ph_value, 2)
    except Exception as e:
        print("pH感測器運作失敗: {}".format(e))
  ```
2. Run the code.
3. Plug the ph sensor into pH4 solution.

![171706_0](https://github.com/a45320614/FishTank_Monitor-Feeding_System/assets/92359154/60814455-f295-45d8-8364-593a4a71f2c3)

4. Set _acidVoltage to return value of ph function.
5. Plug the ph sensor into pH7 solution.

![171707_0](https://github.com/a45320614/FishTank_Monitor-Feeding_System/assets/92359154/dac3e269-837b-49dc-a64f-459eceea8bc4)

6. Set _neutralVoltage to return value of ph function.

### 3. TDS sensor
#### 1. Connect TDS sensor to breadboard.
1. VCC -> 5v
2. GND -> GND
3. Signal -> MCP3008 channel (pick the channel you like, except the channel which already used by pH sensor)

### 4. Water temperature sensor
#### 1. Connect water temperature sensor to breadboard.
1. VCC -> 5v
2. GND -> GND
3. Signal -> GPIO4

### 5. Ultrasonic sensor
- Reference: https://tutorials-raspberrypi.com/raspberry-pi-ultrasonic-sensor-hc-sr04/
- NOTICE: Reference tutorial uses HC-SR04 instead of US-100.
- NOTICE: US-100 have two mode, serial communication and Trigger-Echo, you need to unplug the jumper on the back of the sensor to switch to second mode.

![image](https://github.com/a45320614/FishTank_Monitor-Feeding_System/assets/92359154/1d77bcfa-d460-473e-b823-ad704958b5e8)

![171711_0](https://github.com/a45320614/FishTank_Monitor-Feeding_System/assets/92359154/4584ff4c-e558-4b1f-a78c-ee9fa92c81e9)

#### 1. Connect ultrasonic sensor to breadboard.
1. VCC -> 3.3v (Thus we don't need capacitor)
2. GND -> GND (Two GND are the same)
3. Trig -> GPIO18
4. ECHO -> GPIO26

### 6. 385 Motor & Relay
#### 1. Connect relay to breadboard
1. VCC -> 3.3V
2. GND -> GND
3. IN -> GPIO23 & GPIO 24 (We have two relay)
4. COM -> Battery holder +
   
#### 2. Connect relay to 385 motor
1. NO -> 385 motor +

#### 3. Connect 385 motor to Battery holder
1. 385 motor - -> Battery holder -

![171714_0](https://github.com/a45320614/FishTank_Monitor-Feeding_System/assets/92359154/7198ca24-b52c-40ad-94d3-eca65f81b217)

#### 4. Connect four hose to the motor

![171709_0](https://github.com/a45320614/FishTank_Monitor-Feeding_System/assets/92359154/948c41fe-b2bb-4174-9050-08b0479b51f4)

1. Put the hose in the right container
- You need to distinguish the hose is for in or out.

![171710_0](https://github.com/a45320614/FishTank_Monitor-Feeding_System/assets/92359154/e1f40cec-afe8-42f2-ad5d-73b663eaa994)

### 7. sg90
#### 1. Connect sg90 to breadboard
1. VCC -> 5v
2. GND -> GND
3. signal -> GPIO 13

![171708_0](https://github.com/a45320614/FishTank_Monitor-Feeding_System/assets/92359154/c1bc4c9e-46e3-49cf-817b-a01a8242cddc)

### 8. Camera  
#### 1. Connect Camera to Raspberry Pi
#### 2. Start streaming
```shell
$ cd mjpg-streamer/
$ cd mjpg-streamer-experimental/
$ ./mjpg_streamer -i "./input_uvc.so -d /dev/video0 -n" -o "./output_http.so -p 9000 -w /opt/mjpg-streamer/www"
```

![171713_0](https://github.com/a45320614/FishTank_Monitor-Feeding_System/assets/92359154/b8fa7ed3-57df-4630-89ea-0ad7f09ed9be)

### 9. Web
#### 1. Create your main program
1. Setup the import, GPIO pin, spi, init().
2. Setup the sensor reading function.
3. Setup the motor action function.
4. Setup the value standard conditional statement.
5. Setup the request function.
6. Setup the data writing function.

#### 2. Create your Flask
1. Use subprocess to run main program and app.py simultaneously
```python
import subprocess

fishTankMonitor_process = subprocess.Popen(['python', 'FishTankMonitor.py'])
```
2. Read the data collected from sensors
```python
with open('data_new.txt', 'r') as file:
  lines = file.readlines()
  if lines:
      historicalData = [
          {'pH': float(entry[0]), 'temp': float(entry[1]), 'TDS': float(entry[2]),
           'current_waterLevel': float(entry[3]), 'timeStamp': entry[4]}
          for entry in [line.strip().split(',') for line in lines]
      ]
```
3. Setup the routes
- When you need to do something to main program through your website, you should setup index route or create a new route. 
#### 3. Create your HTML & CSS & javaScript
1. Setup external script file
- Using Chart.js for generate line graph.
- Using Moment.js for date format.
- Using Chart.js Zoom plugin for zoom in the graph.

```html
<script src="https://cdn.jsdelivr.net/npm/moment@2.29.1/moment.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-moment/dist/chartjs-adapter-moment.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom"></script>
```
2. Setup your own HTML and CSS content
3. Generate line graph
4. Create function for feeding and changing water.

### 10. LINE Notification
- Reference: https://hackmd.io/@flagmaker/HkvK0aMDp

![171729](https://github.com/a45320614/FishTank_Monitor-Feeding_System/assets/92359154/2e77ea9f-f8bd-4d63-8411-39db1572ca8e)

#### 1. Using Make instead of ITTT
- Since some of the applets aren't free, I decided to use Make.
- Just follow the steps in the reference tutorial, pretty simple.

## 5. Known issues
