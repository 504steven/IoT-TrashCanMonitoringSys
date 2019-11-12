# WS client example
import json
import os

from random import randint
import websocket
try:
    import thread
except ImportError:
    import _thread as thread
import time
import uuid

from sqlalchemy import create_engine, Column, Integer, String, Boolean, Unicode, UnicodeText
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# create client id
uid = str(uuid.uuid1())

Base = declarative_base()
objects = {}


# resource owned by the client
class ObjectInfo(Base):
    __tablename__ = "objectinfo"
    id = Column(Integer, primary_key=True)
    object_id = Column(Integer)
    resource_id = Column(Integer)
    reading = Column(Integer)


class ClientInfo(Base):
    __tablename__ = "clientinfo"
    id = Column(Integer,primary_key=True)
    client_id = Column(Integer)
    devices = Column(String)

port = 2333
client_id = randint(1,100)
client_name = "robot"
client_type = randint(1,5)
lwm2m_version = 1.0
lifetime = 5
min_period = 10
max_period = 20
instance_id = 1


# creating sql database
engine = create_engine('sqlite:///storage.sqlite')
if not os.path.exists("storage.sqlite"):
    print("CREATING TABLE")
    Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()


doObserve = False

# json to string
def j2s(js):
    return json.dumps(js)


# string to json
def s2j(stn):
    return json.loads(stn)


def startObserve():
    global  doObserve
    doObserve = True


def stopObserve():
    global  doObserve
    doObserve = False

def getClientReading():
    return randint(60,90) # assuming some temperature gauge


def is_json(myjson):
    try:
        json_object = json.loads(myjson)
    except ValueError as e:
        return False
    return True

# receive message from server
def on_message(ws, message):
    if is_json(message):
        packet = s2j(message)
        print("message is ",message)
        if (type(packet) == dict) and 'method' in packet.keys(): # handle messages received from server
            method = packet['method']

            if method == "dr": # bootstrap discover response
                print("following are the neighbours")
                print(packet['neighbours'])

            if method == "create": # server create request
                if client_id == int(packet["client_id"]):
                    print("server read received:", packet["msg"])
                    session.add(ObjectInfo(object_id=packet["o_id"], resource_id=packet["o_id"],reading=packet["val"]))
                    print("resource created")
                    ws.send(json.dumps({"method":"create","client_id":client_id,"status":"success", "msg":"/{}/0/1".format(packet['o_id'])}))
                    session.commit()
            if method == 'read': # server read request
                if client_id == int(packet["client_id"]):
                    print("server read received:",packet["msg"])
                    temp = session.query(ObjectInfo).filter_by(object_id=packet["o_id"]).first()
                    ws.send(json.dumps({"method":"read","client_id":client_id,"reading":temp.reading}))

            if method == 'write': # server write request
                if client_id == int(packet["client_id"]):
                    temp = session.query(ObjectInfo).filter_by(object_id=packet["o_id"]).first()
                    temp.reading = packet["new_v"]
                    print("new reading is {}".format(packet["new_v"]))
                    session.commit()
                    ws.send(json.dumps({"method":"write","client_id":client_id,"status":"ok"}))

            if method == 'execute':
                if client_id == int(packet["client_id"]):
                    object_id = packet["o_id"]
                    if session.query(ObjectInfo).filter_by(object_id=object_id).first():
                        print("Performing operations...")
                        ws.send(json.dumps({"method":"execute","status":"success","client_id":client_id}))
                    else:
                        print("No such object!")
                        ws.send(json.dumps({"method":"execute","status":"failed"}))
                # if cliend_id == packet

            if method == 'delete':
                if client_id == int(packet["client_id"]):
                    temp = session.query(ObjectInfo).filter_by(object_id=packet["o_id"],resource_id=packet["o_id"]).first()
                    session.delete(temp)
                    session.commit()
                    print("resource deleted")
                    ws.send(json.dumps({"method":"delete","status":"success","client_id":client_id}))

            if method == "observe":
                print("begin observe")
                if int(packet["client_id"]) == client_id:
                    print("begin observe")
                    startObserve()
                    thread.start_new_thread(notify,())

            if method == "cancle_observation":
                try:
                    if int(packet["client_id"]) == client_id:
                        stopObserve()
                except ValueError as e:
                    pass
            elif not method:
                pass
        else:
            print("server sent: ",packet)
    else:
        print(message)


def on_error(ws, error):
    print(error)


def on_close(ws):
    pass


def notify():
    print("begin notify")
    while doObserve:
        print("data changed, notifying server")
        ws.send(json.dumps({"method":"notify","client_id":client_id,"reading":randint(60, 80)}))
        time.sleep(randint(5,7))

# discover other devices in system
def bootstrap_discover():
    payload = {"method": "dr","response":"lwm2m=\"1.0\",ssid="+str(client_id)+",</3/0>"}
    ws.send(j2s(payload))


# register device
def bootstrap_write():
    new_id = randint(0,9)
    payload = {"method":"bw","ep":client_name, "oi":3, "ni":new_id,"id":client_id} # bootstrap write
    # print(payload)
    ws.send(j2s(payload))


# remove device in bootstrap
def bootstrap_detele():
    payload = {"method":"bd","ep":client_name,"id":2}  # bootstrap delete
    ws.send(j2s(payload))


def bootstrap_request():
    payload = {"method":"bs","ep":client_name,"client_type":client_type, "id":client_id}
    ws.send(j2s(payload))


def bootstrap_end():
    payload = {"method":"bs","ep":client_name}  # bootstrap end
    ws.send(j2s(payload))
    print("bootstrap end")


def register():
    payload = {"method":"rg","id":client_id,"ep":client_name,"devices":""} #register device
    ws.send(j2s(payload))


def update(): # update for regerting
    print("sending updates")
    new_device = str("<"+str(randint(1,5))+"/"+str(randint(1,6))+">"+"<"+str(randint(1,6))+"/"+str(randint(1,6))+">")
    payload = {"method":"ud","id":client_id,"devices":new_device}
    ws.send(j2s(payload))


def deregister():
    payload = {"method":"ur","ep":client_name,"id":client_id}  # bootstrap end
    ws.send(j2s(payload))


def on_open(ws):
    def run(*args):
        bootstrap()
        register()
        time.sleep(60)

        print("thread terminating...")
    thread.start_new_thread(run, ())


def bootstrap():
    #bootstrap request
    print("begin init bootstrap")
    bootstrap_request()
    bootstrap_discover()
    bootstrap_write()
    bootstrap_detele()
    bootstrap_end()
    print("end init bootstrap")

def userio():
        time.sleep(1)
        while True:
            time.sleep(0.5)
            operation = input("Selection operation: (U)pgrade, (D)owngrade, (P)ay, (A)ccount, (S)tatistics(Premium Only): \n")
            operation = operation.lower()
            if operation in ("u", "upgrade"):
                payload = {"method":"upgrade"}
                ws.send(j2s(payload))
            elif operation in ("d", "downgrade"):
                payload = {"method":"downgrade"}
                ws.send(j2s(payload))
            elif operation in ("p", "pay"):
                amount = int(input("How much do you want to pay?"))
                payload = {"method":"pay", "amount":amount}
                ws.send(j2s(payload))
            elif operation in ("a", "account"):
                payload = {"method":"account"}
                ws.send(j2s(payload))
            
            elif operation in ("s", "statistics"):
                payload = {"method":"stats"}
                ws.send(j2s(payload))
            else:
                print("invalid command")



if __name__ == "__main__":
    websocket.enableTrace(True) #TODO: change to False
    ws = websocket.WebSocketApp("ws://localhost:"+str(port)+"/",
                              on_message = on_message,
                              on_error = on_error,
                              on_close = on_close)
    ws.on_open = on_open
    thread.start_new_thread(userio,())
    ws.run_forever()