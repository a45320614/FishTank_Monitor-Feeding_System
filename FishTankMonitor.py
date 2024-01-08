# -*- coding: utf-8 -*-

import RPi.GPIO as GPIO
import os
import glob
import time
import requests
from datetime import datetime
import spidev
import fcntl

SPICLK = 11
SPIMISO = 9
SPIMOSI = 10
SPICS = 8

# Channel connection of MCP3008
#waterLevel_ch = 0
tds_ch = 0
ph_ch = 1

# Pin of waterMotor
waterMotor1 = 23
waterMotor2 = 24

# Pin of feedMotor
feedMotor1 = 13

# pH
_acidVoltage = 2070
_neutralVoltage = 1535

# waterTemp
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'

# UltraSonic
trigger = 18
echo = 26

spi = spidev.SpiDev()
spi.open(0,0)
spi.max_speed_hz = 1350000

def init():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)    

    # waterMotor
    GPIO.setup(waterMotor1, GPIO.OUT)
    GPIO.setup(waterMotor2, GPIO.OUT)

    # feedMotor
    GPIO.setup(feedMotor1, GPIO.OUT)
    global p
    p = GPIO.PWM(feedMotor1, 50)
    
    # UltraSonicSensor
    GPIO.setup(trigger, GPIO.OUT)
    GPIO.setup(echo, GPIO.IN)

def ReadADC(channel):
    try:
        if ((channel > 7) or (channel < 0)):
            return "Channel錯誤!"
        time.sleep(0.5)
        adc = spi.xfer2([1,(8+channel)<<4,0])
        time.sleep(0.5)
        adc_value = ((adc[1]&3)<<8) + adc[2]
        return adc_value
    except Exception as e:
        print("無法讀取ADC: {}".format(e))
        
# 感測TDS值
def tds():
    try:
        time.sleep(0.1) 
        adc_value = ReadADC(tds_ch)
        voltage = adc_value * 3.3 / 1024.0
        
        if voltage == 0:
            print("Error: Voltage is zero. Cannot calculate TDS.")
            return 0
        
        tds_value = (133.42 / voltage * voltage * voltage - 255.86 * voltage * voltage + 857.39 * voltage) * 0.5
        
        print("TDS value: " + str(tds_value))  
        return round(tds_value, 2)
    except Exception as e:
        print("TDS感測器運作失敗: {}".format(e))

# 感測水溫
def waterTemp():
    try:
        with open(device_file, 'r') as f:
            lines = f.readlines()
        
        while lines[0].strip()[-3:] != 'YES':
            time.sleep(0.2)
            with open(device_file, 'r') as f:
                lines = f.readlines()
                        
        equals_pos = lines[1].find('t=')
        
        if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            temp = float(temp_string) / 1000.0
            print("Celcius temperature: "+ str(temp)) 
            
        return round(temp, 2)
    except Exception as e:
        print("水溫感測器運作失敗: {}".format(e))

# 感測pH值
def ph():
    global _acidVoltage
    global _neutralVoltage
    
    try:
        time.sleep(0.1) 
        adc_value=ReadADC(ph_ch)
        voltage = float(adc_value) * 5
        print("pH sensor的電壓為: " + str(voltage))
        slope = (7.0-4.0)/((_neutralVoltage-1500.0)/3.0 - (_acidVoltage-1500.0)/3.0)
        intercept = 7.0 - slope*(_neutralVoltage-1500.0)/3.0
        ph_value  = slope*(voltage-1500.0)/3.0+intercept
        print("PH value: "+str(ph_value))
        return round(ph_value, 2)
    except Exception as e:
        print("pH感測器運作失敗: {}".format(e))

# 感測水位
def waterLevel():
    try:
        GPIO.output(trigger, GPIO.LOW)
        time.sleep(0.00001)
        GPIO.output(trigger, GPIO.HIGH)
        time.sleep(0.00001)
        GPIO.output(trigger, GPIO.LOW)
        
        while GPIO.input(echo) == 0:
            StartTime = time.time()

        while GPIO.input(echo) == 1:
            StopTime = time.time()
        
        TimeElapsed = StopTime - StartTime
        distance = (TimeElapsed * 34300) / 2
        
        print("Water Level: " + str(12 - distance))
        return round(12 - distance, 2)
    except Exception as e:
        print("超音波感測器運作失敗: {}".format(e))

# 各項數值的標準
def valueStandard(ph_less, ph_greater, temp_less, temp_greater, tds_less, tds_greater, waterLevel_input, bottomSoil, waterWeed):
    global ph_standard_less
    global ph_standard_greater
    global temp_standard_less
    global temp_standard_greater
    global tds_standard_less
    global tds_standard_greater
    global waterLevel_standard

    # 判斷邏輯未完成
    

# 判斷各項數值是否異常，如有異常則向LINE發送通知       
def lineNotify(pH, temp, TDS):
    if(pH > 7 and temp > 20 and TDS > 100):
        sendNotify(pH, temp, TDS)
    elif(pH > 7 and temp > 20 and TDS < 100):
        sendNotify(pH, temp, "無異常")                
    elif(pH > 7 and temp < 20 and TDS < 100):
        sendNotify(pH, "無異常", "無異常")
    elif(pH > 7 and temp < 20 and TDS > 100):                                
        sendNotify(pH, "無異常", TDS)
    elif(pH < 7 and temp < 20 and TDS > 100):                                
        sendNotify("無異常", "無異常", "異常: " + str(TDS))

# 向LINE發送通知    
def sendNotify(pH, temp, TDS):
    make_url = "https://hook.us1.make.com/nbccvhmwxhxdv3ksq4ox9s4zb81yi2a6"
    make_params = {
        'pH': pH,
        'temp': temp,
        'TDS': TDS
    }
    response = requests.get(make_url, params=make_params)

    if response.status_code == 200:
        print("請求成功: {}".format(response.text))
    else:
        print("請求失敗: {} {}".format(response.status_code, response.text))

# 補水    
def waterMotor_IN():
    try:
        GPIO.output(waterMotor2, GPIO.LOW)
    except Exception as e:
        print("抽水馬達2運作失敗: {}".format(e))

# 抽水
def waterMotor_OUT():
    try:
        GPIO.output(waterMotor1, GPIO.LOW)
    except Exception as e:
        print("抽水馬達1運作失敗: {}".format(e))

# 停止抽水馬達1        
def waterMotor1_STOP():
    try:
        GPIO.output(waterMotor1, GPIO.HIGH)
    except Exception as e:
        print("抽水馬達1運作失敗: {}".format(e))

# 停止抽水馬達2           
def waterMotor2_STOP():
    try:
        GPIO.output(waterMotor2, GPIO.HIGH)
    except Exception as e:
        print("抽水馬達2運作失敗: {}".format(e))
    
# 如水位過低，自動啟動抽水馬達補水10秒   
def water_IN(current_waterLevel):
    if(current_waterLevel < 8):
        waterMotor_IN()
        time.sleep(10)
        waterMotor2_STOP()  

# 換水
def changeWater():
    GPIO.setup(waterMotor1, GPIO.OUT)
    GPIO.setup(waterMotor2, GPIO.OUT)
    waterMotor_OUT()
    time.sleep(30)
    waterMotor1_STOP()
    waterMotor_IN()
    time.sleep(30)
    waterMotor2_STOP()

# 餵食馬達        
def feedMotor(p):
    try:
        p.start(0)
        p.ChangeDutyCycle(4)
        p.ChangeDutyCycle(2)
        time.sleep(0.2)
        p.ChangeDutyCycle(4)
        time.sleep(0.1)
        p.ChangeDutyCycle(0)
    except Exception as e:
        print("餵食馬達運作失敗: {}".format(e))

def main():
    init()        
    try:
        while True:
            waterMotor1_STOP()
            waterMotor2_STOP()
            TDS = tds()
            pH = ph()
            current_waterLevel = waterLevel()         
            temp = waterTemp()
            timeStamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 將各項數值寫入文件
            with open('data.txt', 'a') as file:
                fcntl.flock(file, fcntl.LOCK_EX)
                file.write("{},{},{},{},{}\n".format(pH, temp, TDS, current_waterLevel, timeStamp))
            
            water_IN(current_waterLevel)
             
            # 如果有數值出現異常，傳送通知到LINE
            lineNotify(pH, temp, TDS)

            # 多久紀錄一次
            time.sleep(5 * 60)
            
    except KeyboardInterrupt:
        pass
    GPIO.cleanup()

if __name__ == '__main__':
    main()