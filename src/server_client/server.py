'''
# server.py
from flask import Flask, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# 連線車輛記錄： car_id -> session_id
car_sessions = {}

@socketio.on('register')
def handle_register(car_id):
    print(f"[Register] Car ID: {car_id} -> SID: {request.sid}")
    car_sessions[car_id] = request.sid

@socketio.on('disconnect')
def handle_disconnect():
    print(f"[Disconnected] {request.sid}")
    for car_id, sid in list(car_sessions.items()):
        if sid == request.sid:
            del car_sessions[car_id]
            break

@socketio.on('message')
def handle_message(data):
    """
    data is 協定 with client send_to()
    data is a dict = {
        "target_id": target_id: str,
        "payload": message: any
    }
    """
    print(f"[Received Message] {data}")

    target_id = data.get('target_id')  # 想發給誰
    payload = data.get('payload')      # 要發的內容
    aim = data.get('aim')

    if aim == 'txt to json':
        ##call sth for txt to json 
        #payload is txt str
        None
        #payload should change to json at here

    elif aim == 'json to txt':
        ##call sth for json to txt
        #payload is json dict
        None
        #payload should change to txt(str) here

    elif aim == 'transport':
        None

    if target_id and payload:
        target_sid = car_sessions.get(target_id)
        if target_sid:
            socketio.emit('message', payload, room=target_sid)
            print(f"[Forwarded] to {target_id}")
        else:
            print(f"[Warning] Target {target_id} not connected.")
    else:
        print("[Error] Message missing 'target_id' or 'payload'.")

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
'''

# server.py
from flask import Flask, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# 連線車輛記錄： car_id -> session_id
car_sessions = {}

def announceAll_connect(car_id: str):
    """
    Announce to all other connected cars that a new car has joined.
    """
    for target_id, sid in car_sessions.items():
        if target_id != car_id:
            payload = {
                "correctness": True,
                "來自的車牌號碼": "server",
                "傳給的車牌號碼": target_id,
                "傳達訊息": (car_id, "add") #important
            }
            socketio.emit('message', payload, room=sid)
    print(f"[Announce] {car_id} joined, broadcasted to all other cars.")

def announceAll_disconnect(car_id: str):
    """
    Announce to all other connected cars that a car has left.
    """
    for target_id, sid in car_sessions.items():
        if target_id != car_id:
            payload = {
                "correctness": True,
                "來自的車牌號碼": "server",
                "傳給的車牌號碼": target_id,
                "傳達訊息": (car_id, "delete")
            }
            socketio.emit('message', payload, room=sid)
    print(f"[Announce] {car_id} left, broadcasted to all other cars.")

def include_all_online(car_id: str):
    """
    Send a message to the newly joined car listing all currently online car IDs (excluding itself).
    """
    sid = car_sessions.get(car_id)
    if not sid:
        print(f"[Error] include_all_online: SID not found for {car_id}")
        return

    online_cars = [cid for cid in car_sessions if cid != car_id]
    if not online_cars:
        return
    payload = {
        "correctness": True,
        "來自的車牌號碼": "server",
        "傳給的車牌號碼": car_id,
        "傳達訊息": (online_cars, "include") # online_cars is a list of str
    }
    socketio.emit('message', payload, room=sid)
    print(f"[Info] Sent online car list to {car_id}: {online_cars}")


@socketio.on('register')
def handle_register(car_id):
    print(f"[Register] Car ID: {car_id} -> SID: {request.sid}")
    announceAll_connect(car_id)
    car_sessions[car_id] = request.sid
    include_all_online(car_id)    # 告訴新加入的車目前在線的是誰

@socketio.on('disconnect')
def handle_disconnect():
    print(f"[Disconnected] {request.sid}")
    for car_id, sid in list(car_sessions.items()):
        if sid == request.sid:
            del car_sessions[car_id]
            announceAll_disconnect(car_id)
            break

@socketio.on('message')
def handle_message(data):
    """
    data is 協定 with client send_to()
    data is a dict = {
        "target_id": target_id: str,
        "payload": message: should be a json = {"correctness":, "來自的車牌號碼":, "傳給的車牌號碼":, "傳達訊息":}
    }
    """
    print(f"[Received Message] {data}")

    target_id = data.get('target_id')  # 想發給誰
    payload = data.get('payload')      # 要發的內容
    aim = data.get('aim')

    if aim == 'txt to json':
        ##call sth for txt to json 
        #payload is txt str
        None
        #payload should change to json at here

    elif aim == 'json to txt':
        ##call sth for json to txt
        #payload is json dict
        None
        #payload should change to txt(str) here

    elif aim == 'transport':
        None

    if target_id and payload:
        target_sid = car_sessions.get(target_id)
        if target_sid:
            socketio.emit('message', payload, room=target_sid)
            print(f"[Forwarded] to {target_id}")
        else:
            print(f"[Warning] Target {target_id} not connected.")
    else:
        print("[Error] Message missing 'target_id' or 'payload'.")

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
