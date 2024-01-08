from flask import Flask, render_template, request
import time
import FishTankMonitor
import subprocess
from datetime import datetime
import RPi.GPIO as GPIO
import threading

app = Flask(__name__)

fishTankMonitor_process = subprocess.Popen(['python', 'FishTankMonitor.py'])

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
feedMotor1 = 13
GPIO.setup(feedMotor1, GPIO.OUT)
p = GPIO.PWM(feedMotor1, 50)

historicalData = []

sensor_data = {
    'pH': 0.0,
    'temp': 0.0,
    'TDS': 0.0,
    'current_waterLevel': 0,
    'timeStamp': datetime.now()
}

def simulate_data_update():
    data_lock = threading.Lock()
    global historicalData

    while True:
        try:         
            # 讀取資料
            with open('data_new.txt', 'r') as file:
                lines = file.readlines()
                if lines:
                    historicalData = [
                        {'pH': float(entry[0]), 'temp': float(entry[1]), 'TDS': float(entry[2]),
                         'current_waterLevel': float(entry[3]), 'timeStamp': entry[4]}
                        for entry in [line.strip().split(',') for line in lines]
                    ]
                    
                    latest_entry = lines[-1].strip().split(',')
                    timeStamp_str = latest_entry[-1]
                    latest_entry.pop()
                    pH, temp, TDS, current_waterLevel = map(float, latest_entry)
                    timeStamp = datetime.strptime(timeStamp_str, '%Y-%m-%d %H:%M:%S')

            with data_lock:
                sensor_data['pH'] = pH
                sensor_data['temp'] = temp
                sensor_data['TDS'] = TDS
                sensor_data['current_waterLevel'] = current_waterLevel
                sensor_data['timeStamp'] = timeStamp
                print(f"Read sensor data: pH={pH}, temp={temp}, TDS={TDS}, current_waterLevel={current_waterLevel}, timeStamp={timeStamp}")
        except Exception as e:
            print(f"Error reading sensor data: {e}")

        # 抓取的數值多久更新一次
        time.sleep(5 * 60)

import threading
update_thread = threading.Thread(target=simulate_data_update)
update_thread.start()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        ph_less = request.form['ph_less']
        ph_greater = request.form['ph_greater']        
        temp_less = request.form['temp_less']
        temp_greater = request.form['temp_greater']        
        tds_less = request.form['tds_less']
        tds_greater = request.form['tds_greater']        
        waterLevel_input = request.form['waterLevel_input']
        bottomSoil = request.form['bottomSoil']
        waterWeed = request.form['waterWeed']
        
        return '成功自訂數值!'
    return render_template('index.html', sensor_data = sensor_data, historicalData = historicalData)

@app.route('/feed')
def feed_motor():
    FishTankMonitor.feedMotor(p)
    return '成功餵食!'

@app.route('/changeWater')
def changeWater():
    FishTankMonitor.changeWater()
    return '成功換水!'

if __name__ == '__main__':
    app.run(port=5000, threaded=True)