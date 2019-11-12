import json
import math
import time
import uuid
import random
import datetime

try:
    import thread
except ImportError:
    import _thread as thread

import socketio
import datetime

start_time = time.time()
sio = socketio.Client()
lat = 40.782743 + random.uniform(-1, 1)*0.003
lng = -73.966138 + random.uniform(-1, 1)*0.003
max_weight = 50
client_id = None


# get client id from server
@sio.on('get_id')
def get_id(data):
    print("get id:", data)
    global client_id

    client_id = 'client_id:' + str(data['id'])

def get_percentage(num):
    return num/max_weight


@sio.on('connect')
def on_connect():
    print("connecting")
    sio.emit("init_client", {})


@sio.on('get_reading')
def on_get_reading(data):
    print('get reading')
    sio.emit("return_reading", data=get_data())


@sio.on('message')
def on_message(data):
    print("data from server:", data)


@sio.on('disconnect')
def on_disconnect():
    sio.emit("dc_client", {"id": client_id})
    print('I\'m disconnected!')


def get_data():
    elapsed_time = time.time() - start_time
    # seconds = elapsed_time % 60
    # relastic weight
    # print('seconds',seconds)
    # weight = 125*math.sin(5*random()+seconds/(math.pi*10))+125
    weight = elapsed_time/6 + random.uniform(-1, 1)*0.5
    print("weight:", weight)

    print("weight: {}, percentage: {}".format(weight, get_percentage(weight)))
    now = '{0:%Y-%m-%dT%H:%M:%S}'.format(datetime.datetime.now())
    print("sensor data date and time:",now)
    return {"id": client_id, "lat": lat, "lng": lng, "weight": weight, "percentage": get_percentage(weight), "time": now}


# send heartbeat to server
def beep(*args):
    wait_time = 5
    now = '{0:%S}'.format(datetime.datetime.now())
    while int(now) % 5 != 0:
        now = '{0:%S}'.format(datetime.datetime.now())
        print("time:", now, int(now) % 5 )
    while True:
        print("report in {} seconds".format(wait_time))
        cur_data = get_data()
        sio.emit("return_data", data=cur_data)
        print(cur_data)
        time.sleep(wait_time)
        # sio.emit("heartbeat",{"id":client_id})


sio.connect('http://localhost:80/')
print("client id:", client_id)
while True: 
    if client_id != None:
        break
thread.start_new_thread(beep, ())
