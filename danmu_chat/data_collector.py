from pydouyu.client import Client
from datetime import datetime

def chatmsg_handler(msg, room_id, db_queue):
    msg['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    msg['room_id'] = room_id
    db_queue.put(msg)
    output = msg['timestamp'] + " " + msg['nn'] + ": " + msg['txt']
    print(output)

def data_collector(room_id, db_queue):
    c = Client(room_id=room_id)
    c.add_handler('chatmsg', lambda msg: chatmsg_handler(msg, room_id, db_queue))
    c.start()
