from pydouyu.client import Client
import time
import sys
import sqlite3
from threading import local, Thread
from queue import Queue
import matplotlib.pyplot as plt

class DB:
    def __init__(self, db_name):
        self.db_name = db_name
        self.local_data = local()
        self.initialize_db()

    def get_conn(self):
        if not hasattr(self.local_data, "conn"):
            self.local_data.conn = sqlite3.connect(self.db_name)
        return self.local_data.conn

    def store_msg(self, msg):
        conn = self.get_conn()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO chat_messages (user, message, timestamp) VALUES (?, ?, ?)",
                       (msg['nn'], msg['txt'], time.time()))
        conn.commit()

    def initialize_db(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY,
            user TEXT,
            message TEXT,
            timestamp REAL)
        ''')
        conn.commit()


db = DB("chat_messages.db")

count_queue = Queue()
times = []
counts = []

def chatmsg_handler(msg):
    db.store_msg(msg)
    count_queue.put(1)  # Push a count into the queue
    output = time.strftime("[%Y-%m-%d %H:%M:%S] ", time.localtime()) + msg['nn'] + ": " + msg['txt']
    print(output)
    sys.stdout.flush()

def uenter_handler(msg):
    output = time.strftime("[%Y-%m-%d %H:%M:%S] ", time.localtime()) + msg['nn'] + " 进入了直播间"
    print(output)
    sys.stdout.flush()

def live_plot():
    plt.ion()
    while True:
        count = 0
        start_time = time.time()
        while time.time() - start_time < 30:
            while not count_queue.empty():
                count += count_queue.get()
            time.sleep(1)
        times.append(time.strftime("%H:%M:%S", time.localtime()))
        counts.append(count)
        plt.clf()
        plt.plot(times, counts)
        plt.draw()
        plt.pause(0.1)

plot_thread = Thread(target=live_plot)

c = Client(room_id=52876)
c.add_handler('chatmsg', chatmsg_handler)
c.add_handler('uenter', uenter_handler)
plot_thread.start()
c.start()
