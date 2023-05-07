import multiprocessing
import queue
import time
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from datetime import datetime, timedelta
import matplotlib.dates as mdates
from multiprocessing import Manager

from pydouyu.client import Client
import sqlite3

# Queues for sharing data between threads
db_queue = multiprocessing.Queue()
shared_queue = multiprocessing.Queue()

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

def chatmsg_handler(msg, temp_messages):
    msg['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    db_queue.put(msg)
    temp_messages.append(msg)
    output = time.strftime("[%Y-%m-%d %H:%M:%S] ", time.localtime()) + msg['nn'] + ": " + msg['txt']
    print(output)

def data_collector(room_id, temp_messages):
    c = Client(room_id=room_id)
    c.add_handler('chatmsg', lambda msg: chatmsg_handler(msg, temp_messages))
    c.start()

def plotter(temp_messages):
    fig, ax = plt.subplots()
    xdata, ydata = [], []
    ln, = plt.plot([], [], 'r-', animated=False)

    def init():
        ax.set_xlim([datetime.now() - timedelta(minutes=5), datetime.now()])
        ax.set_ylim(0, 100)
        return ln,

    def update(frame):
        now = datetime.now()
        delta = timedelta(seconds=10)
        counter = sum(1 for msg in temp_messages if now - datetime.strptime(msg['timestamp'], '%Y-%m-%d %H:%M:%S') <= delta)

        xdata.append(datetime.now())  # append current time
        ydata.append(counter)
        print(counter)
        if len(xdata) > 10:  # limit the length of data
            xdata.pop(0)
            ydata.pop(0)

        ln.set_data(xdata, ydata)
        ax.set_xlim(min(xdata), max(xdata))
        ax.set_ylim(min(ydata), max(ydata))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        return ln,

    # Start the animation
    ani = FuncAnimation(fig, update, frames=None, init_func=init, interval=10000, blit=False, repeat=True)
    plt.show()

if __name__ == '__main__':
    with Manager() as manager:
        # Create a shared list for storing messages in a 10-second interval
        temp_messages = manager.list()

        # Start the database worker thread
        db_thread = multiprocessing.Process(target=db_worker)
        db_thread.start()

        # Start the data collector thread
        room_id = 762484  # replace with your room id
        collector_thread = multiprocessing.Process(target=data_collector, args=(room_id, temp_messages))
        collector_thread.start()

        # Start the plotter in the main thread
        plotter(temp_messages)

        # Send exit signal to the database worker thread
        db_queue.put(None)
        db_thread.join()

        # Terminate the other processes
        collector_thread.terminate()
