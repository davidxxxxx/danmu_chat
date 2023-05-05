import threading
import queue
import time
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.animation import FuncAnimation
from matplotlib.dates import date2num, DateFormatter
from collections import deque
from datetime import datetime, timedelta

from pydouyu.client import Client
import sqlite3

# Queues for sharing data between threads
data_queue = queue.Queue()
db_queue = queue.Queue()

# Deque for storing messages
messages = deque()

def db_worker():
    conn = sqlite3.connect('danmu.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY,
            user TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp TIMESTAMP NOT NULL
        );
    ''')

    while True:
        msg = db_queue.get()
        if msg is None:  # exit signal
            break
        cursor.execute("INSERT INTO chat_messages (user, message, timestamp) VALUES (?, ?, ?)",
                       (msg['nn'], msg['txt'], datetime.now()))
        conn.commit()

    conn.close()

def chatmsg_handler(msg):
    msg['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    db_queue.put(msg)
    messages.append(msg)
    output = time.strftime("[%Y-%m-%d %H:%M:%S] ", time.localtime()) + msg['nn'] + ": " + msg['txt']
    print(output)

def data_collector(room_id):
    c = Client(room_id=room_id)
    c.add_handler('chatmsg', chatmsg_handler)
    c.start()


def plotter():
    fig, ax = plt.subplots()
    xdata, ydata = [], []
    ln, = plt.plot([], [], 'r-')

    def count_per_interval(interval):
        now = datetime.now()
        delta = timedelta(seconds=interval)
        counter = 0
        while len(messages) > 0:  # as long as there are messages left
            timestamp_str = messages[0].get('timestamp')
            if timestamp_str is not None:
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                if now - timestamp <= delta:
                    counter += 1
                    messages.popleft()  # remove this message
                else:
                    break  # if this message is out of interval, so are the rest
        return counter

    def init():
        ax.set_ylim(0, 5)
        ax.set_xlim([datetime.now(), datetime.now() + timedelta(seconds=30)])
        del xdata[:]
        del ydata[:]
        return ln,

    def update(frame):
        counter = count_per_interval(30)
        xdata.append(datetime.now())  # append current time
        ydata.append(counter)
        ln.set_data(xdata, ydata)
        ax.relim()
        ax.autoscale_view()
        ax.xaxis_date()
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        ax.yaxis.get_major_locator().set_params(integer=True)  # ensure y-axis uses integer ticks
        return ln,
  #  ani = FuncAnimation(fig, update, interval=30000, blit=True, cache_frame_data=False)

    ani = FuncAnimation(fig, init_func=init, func=update, frames=None, interval=30000, blit=True)
    plt.show()


db_thread = threading.Thread(target=db_worker)
db_thread.start()

room_id = 73965  # replace with your room id
collector_thread = threading.Thread(target=data_collector, args=(room_id,))
collector_thread.start()

plotter()

db_queue.put(None)
db_thread.join()
