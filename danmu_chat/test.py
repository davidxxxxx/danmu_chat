import threading
import queue
import time
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import deque
from datetime import datetime, timedelta
import matplotlib.dates as mdates

from pydouyu.client import Client
import sqlite3

# Queues for sharing data between threads
data_queue = queue.Queue()
db_queue = queue.Queue()
messages = deque()

def db_worker():
    # Database setup
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
    db_queue.put(msg)
    data_queue.put(msg)
    output = time.strftime("[%Y-%m-%d %H:%M:%S] ", time.localtime()) + msg['nn'] + ": " + msg['txt']
    print(output)

def data_collector(room_id):
    c = Client(room_id=room_id)
    c.add_handler('chatmsg', chatmsg_handler)
    c.start()

def plotter():
    fig, ax = plt.subplots()
    xdata, ydata = [], []
    ln, = plt.plot([], [], 'r-', animated=True)

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
        ax.set_xlim([datetime.now() - timedelta(minutes=5), datetime.now()])
        ax.set_ylim(0, 100)
        return ln,

    def update(frame):
        xdata.append(datetime.now())  # append current time
        ydata.append(count_per_interval(30))
        if len(xdata) > 10:  # limit the length of data
            xdata.pop(0)
            ydata.pop(0)

        ln.set_data(xdata, ydata)
        ax.relim()
        ax.autoscale_view(scalex=False)  # only autoscale y-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        return ln,

    # Start the animation
    ani = FuncAnimation(fig, update, frames=None, init_func=init, interval=30000, blit=True, repeat=True)
    plt.show()

def process_queue():
    while True:
        try:
            msg = data_queue.get(timeout=1)
            msg['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            messages.append(msg)
        except queue.Empty:
            pass

# Start the database worker thread
db_thread = threading.Thread(target=db_worker)
db_thread.start()

# Start the data collector thread
room_id = 88660  # replace with your room id
collector_thread = threading.Thread(target=data_collector, args=(room_id,))
collector_thread.start()

# Start the queue processing thread
process_thread = threading.Thread(target=process_queue)
process_thread.start()

# Start the plotter in the main thread
plotter()

# Send exit signal to the database worker thread
db_queue.put(None)
db_thread.join()

