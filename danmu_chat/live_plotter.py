import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from datetime import datetime, timedelta
import matplotlib.dates as mdates

def live_plotter(room_id, message_queue):
    fig, ax = plt.subplots()
    xdata, ydata = [], []
    ln, = plt.plot([], [], 'r*-', animated=False)

    def init():
        ax.set_xlim([datetime.now(),datetime.now() + timedelta(minutes=5)])
        ax.set_ylim(0, 100)
        return ln,

    def update(frame):
        now = datetime.now()
        delta = timedelta(seconds=10)

        # Get messages from the queue
        temp_messages = []
        while not message_queue.empty():
            temp_messages.append(message_queue.get())

        counter = sum(1 for msg in temp_messages if now - datetime.strptime(msg['timestamp'], '%Y-%m-%d %H:%M:%S') <= delta)

        xdata.append(datetime.now())  # append current time
        ydata.append(counter)
        print(counter)
        if len(xdata) > 10:  # limit the length of data
            xdata.pop(0)
            ydata.pop(0)

        ln.set_data(xdata, ydata)

        if len(xdata) > 1 and len(ydata) > 1:
            ax.set_xlim(min(xdata), max(xdata))
            ax.set_ylim(min(ydata)-5, max(ydata)+5)  # Add a small margin to the limits of the y-axis

        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        return ln,

    # Set axis labels and title
    ax.set_xlabel('Real-time')
    ax.set_ylabel('Danmu counts')
    ax.set_title(f'Monitoring Room {room_id}')

    # Start the animation
    ani = FuncAnimation(fig, update, frames=None, init_func=init, interval=10000, blit=False, repeat=True, cache_frame_data=False)
    plt.show()
