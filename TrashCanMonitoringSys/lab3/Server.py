import json
import time
import pymongo
try:
    import thread
except ImportError:
    import _thread as thread
from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket
import sendEmail

# init server information
server_id = 101
lifetime = 10  # mandatory
min_period = 5  # optional
max_period = 9  # optional
disable = "False"  # optional
disable_timeout = 10  # optional
notification_storing_when_offline = False # mandatory
binding = "bind"  # mandatory
registration_trigger  = "trigger"  # mandatory
firmware_update = "firm"  # optional
clients = []

# init client info db
myDbClient = pymongo.MongoClient('mongodb://localhost:27017/')
mydb = myDbClient['dev']
myClients = mydb["client"]
myPayment = mydb["payment"]
clientResource = mydb["resource"]
collist = mydb.list_collection_names()
print(collist)

#clear db
myClients.drop()
clientResource.drop()

def j2s(js):
    return json.dumps(js)

# string to json
def s2j(stn):
    return json.loads(stn)

port = 2333

class BaseServer(WebSocket):

    def handleMessage(self):
        # echo message back to client
        # print("self.data is ",self.data)
        data = s2j(self.data)
        self.reqs += 1
        self.ress += 1

        if (type(data) == dict) and 'method' in data.keys():
            # change reply based on type
            method = data["method"]
            if method == "bs":  # begin bootstrap or end boostrap
                if "id" in data.keys(): # begin boostrap
                    print("begin bootstrap")
                    client_id = data["id"]
                    new_client = {"client_id":client_id,"client_name":data["ep"],"client_type":data["client_type"]}
                    new_account = {"client_id":client_id, "isPremium":False, "balance":0}
                    myClients.insert_one(new_client)
                    myPayment.insert_one(new_account)
                    self.sendMessage(json.dumps("GET "+str(client_id)+"/"))
                else:  # end bootstrap
                    print("end bootstrap")
                    print("client",data["ep"],"finished init")
                    self.sendMessage(json.dumps({"method":"bs"}))

            elif method == "bw": # begin bootstrap write
                client_name = data["ep"]
                print("write operation received from", client_name)
                new_Client = {"client_name":data["ep"],"client_type":data["ni"], "client_id":data["id"]}
                # myClients.replace_one({"clent_name": data["ep"]}, new_Client, upsert=True)
                print("updated database")
                self.sendMessage(json.dumps({"method": "bs"}))

            elif method == "bd":  # bootstrap delete
                client_name = data["ep"]
                print("delete operation for client",client_name)
                self.sendMessage(json.dumps({"method": "bd"}))

            elif method == "dr":  # discover response
                neighbours = []
                for i in myClients.find({}, {"_id": 0}):
                    neighbours.append(i)
                print(data["response"])
                print("currently registered devices:",neighbours)
                packet = {"method":"dr","neighbours":neighbours}
                self.sendMessage(json.dumps(packet))

            elif method == "rg":  # register
                client_id = data["id"]
                myClients.update_one({"client_id":client_id},{
                    "$set": {
                        "devices":data['devices'],
                    }
                },upsert=True)
                print("client",client_id,"registered")
                neighbours = []
                for i in myClients.find({}, {"_id": 0}):
                    neighbours.append(i)
                print("currently registered devices:",neighbours)
                self.sendMessage(json.dumps(2.01))

            elif method == "ud":  # update
                client_id = data["id"]
                myClients.update_one({"client_id":client_id},{
                    "$set": {
                        "devices":data['devices'],
                    }
                },upsert=True)
                self.sendMessage(json.dumps(2.04))

            elif method == "ur":  # deregister
                myQuery = {"client_id": data["id"]}
                myClients.delete_many(myQuery)
                neighbours = []
                for i in myClients.find({}, {"_id": 0}):
                    neighbours.append(i)
                print("currently registered devices:",neighbours)
                self.sendMessage(json.dumps(2.02))

            elif method == "read": # read response from client
                print("client {} reading is: {}.".format(data['client_id'],data['reading']))

            elif method == "create":  # create response from client
                print("client {} create:{}".format(data["client_id"],data["status"]))

            elif method == "write":
                print("client {} write: {}".format(data["client_id"],data["status"]))

            elif method == "execute":
                print("client {} execution status: {}".format(data["client_id"],data["status"]))

            elif method == "delete":
                print("client {} delete status: {}".format(data["client_id"],data["status"]))

            elif method == "notify":
                print("client {} notify:{}".format(data["client_id"],data["reading"]))

            elif method == "upgrade":
                self.isPremium = True
                self.sendMessage("upgraded")

            elif method == "downgrade":
                self.isPremium = False
                self.sendMessage("downgraded")

            elif method == "pay":
                payment = int(data["amount"])
                if payment <= 0:
                    self.sendMessage("Not even close")
                else:
                    self.balance -= payment
                self.sendMessage(json.dumps({"balance": self.balance}))

            elif method == "account":
                self.sendMessage(json.dumps({"premium": self.isPremium, "balance": self.balance}))
                self.ress += 1
                sendEmail.sendemail( self.balance, self.reqs, self.ress, self.isPremium)

            elif method == "stats":
                if self.isPremium:
                    self.sendMessage(json.dumps({"NumofRequests": self.reqs, "NumofResponses": self.ress}))

                else:
                    self.sendMessage("You are not premium user.")

            else:
                print("error")
                self.sendMessage(json.dumps({"status":"error"}))
        else:
            print(data)

    def handleConnected(self):
        thread.start_new_thread(self.userio,())
        print(self.address, 'connected')


        self.balance = 0
        self.isPremium = False
        self.reqs = 0
        self.ress = 0

    def handleClose(self):
        print(self.address, 'closed')

    def read(self, cid, o_id):
        msg = "READ /{}/0/0".format(cid)
        package = {"method":"read","client_id":cid,"o_id":o_id,"msg":msg}
        print(msg)
        self.sendMessage(json.dumps(package))
        pass

    def write(self, cid, oid, newv):
        msg = "Write /{}/0/{} {}".format(cid,oid, newv)
        package = {"method":"write","client_id":cid, "o_id":oid,"new_v":newv, "msg":msg}
        self.sendMessage(json.dumps(package))

    def create(self, cid, oid, new_value):
        msg = "Create /{}/0/{} {}".format(cid,oid,new_value)
        package = {"method":"create","client_id":cid, "o_id":oid,"val":new_value, "msg":msg}
        self.sendMessage(json.dumps(package))

    def delete(self, cid, oid):
        package ={"method":"delete","client_id":cid, "o_id":oid}
        self.sendMessage(json.dumps(package))

    def execute(self, cid, oid):
        package = {"method":"execute","client_id":cid,"o_id":oid}
        self.sendMessage(json.dumps(package))
        pass



    def observe(self,cid, iid):
        x = myClients.find_one({"client_id": cid})
        msg =  "OBSERVE /{}/0/{}".format(cid, iid)
        packet = {"method":"observe","client_id":cid, "i_id":iid,"msg":msg}
        print(msg)
        self.sendMessage(json.dumps(packet))

    def cancle_observe(self, cid):
        package = {"method":"cancle_observation","client_id":cid}
        self.sendMessage(json.dumps(package))

    # user control
    def userio(self):
        time.sleep(1)
        while True:
            time.sleep(0.5)
            print("-"*20)
            print("Connected Clients:")
            for i in myClients.find({}, {"_id": 0}):
                print(i)
            c_id = input("Select client id:\n")
            operation = input("Selection operation: (C)reate/(D)elete/(W)rite/(R)ead/(E)xecute/(O)bserve/(X)Cancel observation/(B)ill")
            operation = operation.lower()
            if operation in ("c", "create"):
                o_id = int(input("Input object id:\n"))
                val = int(input("Input value:\n"))
                self.create(c_id,o_id,val)

            elif operation in ("d", "delete"):
                o_id = int(input("Input object id:\n"))
                self.delete(c_id,o_id)

            elif operation in ("w", "write"):
                o_id = input("Input object id:\n")
                val = input("Input value:\n")
                self.write(c_id,o_id,val)

            elif operation in ("r", "read"):
                o_id = int(input("Input object id:\n"))
                self.read(c_id, o_id)

            elif operation in ("e","execute"):
                o_id = input("Input object id:\n")
                self.execute(c_id,o_id)

            elif operation in ("o", "observe"):
                o_id = input("Input object id:\n")
                print("begin observe")
                self.observe(c_id,o_id)

            elif operation in ("x", "cancle"):
                print("Canceling notify")
                self.cancle_observe(c_id)
            
            elif operation in ("b", "bill"):
                print("billing")
                amount = float(input("Amount:\n"))
                self.balance += amount

            else:
                print("invalid command")


server = SimpleWebSocketServer('', port, BaseServer)

print("starting server")
server.serveforever()
