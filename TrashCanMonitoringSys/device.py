import time
import random
import datetime
import socketio
import _thread as thread
import DataFromArduino

start_time = time.time()
sio = socketio.Client()
lat = 37.335246 + random.uniform(-1, 1)*0.002
lng = -121.881199 + random.uniform(-1, 1)*0.
max_dis = 100
client_id = None
rate = 1;

#  init device  to server  when socket is connected
@sio.on('connect')
def on_connect():
    print("register device to server")
    sio.emit("init_device_on_server", {})


#  remove device on server  when socket is dis-connected
@sio.on('disconnect')
def on_disconnect():
    sio.emit("dc_client", {"id": client_id})
    print('I\'m disconnected!')


# assign client id by server
@sio.on('assign_id_to_device')
def get_id(data):
    global client_id
    client_id = 'client_id:' + str(data['id'])


# get cur data and send to server
@sio.on('get_cur_reading_from_device')
def get_cur_reading(data):
    print('get reading')
    sio.emit("return_reading_to_server", data=get_simulated_data())


# send heartbeat to server
def auto_report_data(*args):
    wait_time = 5
    now = '{0:%S}'.format(datetime.datetime.now())
    while int(now) % 5 != 0:
        now = '{0:%S}'.format(datetime.datetime.now())
    while True:
        sio.emit("auto_return_data", data=get_simulated_data())
        time.sleep(wait_time)
    # print("report in {} seconds".format(wait_time), "data:", cur_data)


def get_percentage(num):
    return num/max_dis


def get_data_from_Arduino():
    data = DataFromArduino.get_sensor_data()
    now = '{0:%Y-%m-%dT%H:%M:%S}'.format(datetime.datetime.now())
    print("sensor data date and time:",now)
    return {"id": client_id, "lat": lat, "lng": lng, "weight": data[0]*rate, "percentage": get_percentage(data[1])*rate, "time": now }


def get_simulated_data():
    elapsed_time = time.time() - start_time
    # relative weight
    # weight = 125*math.sin(5*random()+seconds/(math.pi*10))+125
    weight = elapsed_time/6 + random.uniform(-1, 1)*0.5
    print("weight: {}, percentage: {}".format(weight, get_percentage(weight)))
    now = '{0:%Y-%m-%dT%H:%M:%S}'.format(datetime.datetime.now())
    print("sensor data date and time:",now)
    return {"id": client_id, "lat": lat, "lng": lng, "weight": weight, "percentage": get_percentage(weight), "time": now }


sio.connect('http://localhost:3000/')
while True: 
    if client_id != None:
        break
print("assigned client id:", client_id)
thread.start_new_thread(auto_report_data, ())

