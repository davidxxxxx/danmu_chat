import sqlite3
import multiprocessing

def create_connection():
    conn = sqlite3.connect('danmu.db')
    return conn

def create_table(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY,
            room_id INTEGER NOT NULL,
            user TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp TIMESTAMP NOT NULL
        );
    ''')
    conn.commit()

def insert_message(conn, room_id, user, message, timestamp):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat_messages (room_id, user, message, timestamp) VALUES (?, ?, ?, ?)",
                   (room_id, user, message, timestamp))
    conn.commit()

def db_worker(db_queue):
    conn = create_connection()
    create_table(conn)

    while True:
        msg = db_queue.get()
        if msg is None:  # exit signal
            break
        insert_message(conn, msg['room_id'], msg['nn'], msg['txt'], msg['timestamp'])

    conn.close()

def start_db_worker():
    db_queue = multiprocessing.Queue()
    db_thread = multiprocessing.Process(target=db_worker, args=(db_queue,))
    db_thread.start()
    return db_queue, db_thread
