import multiprocessing
from gui import start_gui
from backend import start_backend
from database import start_db_worker

if __name__ == '__main__':

    # Start the database worker thread
    db_queue, db_thread = start_db_worker()

    # Start the backend server
    backend_thread = multiprocessing.Process(target=start_backend, args=(db_queue,))

    backend_thread.start()

    # Start the GUI
    start_gui()

    # Join the database worker thread and backend thread
    db_thread.join()
    backend_thread.join()

    # Send exit signal to the database worker thread
    db_queue.put(None)
