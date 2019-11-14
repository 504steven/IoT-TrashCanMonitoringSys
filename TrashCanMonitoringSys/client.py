import time
import random
import datetime
import socketio
import _thread as thread
import DataFromArduino

start_time = time.time()
sio = socketio.Client()
lat = 40.782743 + random.uniform(-1, 1)*0.003
lng = -73.966138 + random.uniform(-1, 1)*0.003
max_weight = 100
client_id = None

#  device connect to server
@sio.on('connect')
def on_connect():
    print("connecting to server")
    sio.emit("init_client", {})


# get client id from server
@sio.on('get_id')
def get_id(data):
    print("get id:", data)
    global client_id
    client_id = 'client_id:' + str(data['id'])


# get cur data and send to server
@sio.on('get_reading')
def on_get_reading(data):
    print('get reading')
    sio.emit("return_reading", data=get_data())


# @sio.on('message')
# def on_message(data):
#     print("data from server:", data)


@sio.on('disconnect')
def on_disconnect():
    sio.emit("dc_client", {"id": client_id})
    print('I\'m disconnected!')


# send heartbeat to server
def beep(*args):
    wait_time = 5
    now = '{0:%S}'.format(datetime.datetime.now())
    while int(now) % 5 != 0:
        now = '{0:%S}'.format(datetime.datetime.now())
    print("time:", now, int(now) % 5)
    cur_data = get_data()
    sio.emit("return_data", data=cur_data)
    time.sleep(wait_time)
    # print("report in {} seconds".format(wait_time), "data:", cur_data)


def get_percentage(num):
    return num/max_weight


def get_data_from_Arduino():
    dis = DataFromArduino.get_sensor_data()
    now = '{0:%Y-%m-%dT%H:%M:%S}'.format(datetime.datetime.now())
    print("sensor data date and time:",now)
    return {"id": client_id, "lat": lat, "lng": lng, "weight": dis, "percentage": get_percentage(dis), "time": now }


def get_data():
    elapsed_time = time.time() - start_time
    # relative weight
    # weight = 125*math.sin(5*random()+seconds/(math.pi*10))+125
    weight = elapsed_time/6 + random.uniform(-1, 1)*0.5
    print("weight: {}, percentage: {}".format(weight, get_percentage(weight)))
    now = '{0:%Y-%m-%dT%H:%M:%S}'.format(datetime.datetime.now())
    print("sensor data date and time:",now)
    return {"id": client_id, "lat": lat, "lng": lng, "weight": weight, "percentage": get_percentage(weight), "time": now }


sio.connect('http://localhost:3000/')
print("assigned client id:", client_id)
while True: 
    if client_id != None:
        break
thread.start_new_thread(beep, ())

