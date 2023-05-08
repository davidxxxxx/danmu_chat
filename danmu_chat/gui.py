from http.client import responses
import tkinter as tk
from tkinter import messagebox
import requests

class ChatRoomMonitoringGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Chat Room Monitoring")
        self.configure(padx=10, pady=10)

        self.room_id_label = tk.Label(self, text="Enter Room ID:")
        self.room_id_label.grid(row=0, column=0, sticky="e")

        self.room_id_entry = tk.Entry(self)
        self.room_id_entry.grid(row=0, column=1)

        self.add_room_button = tk.Button(self, text="Start Monitoring", command=self.start_monitoring)
        self.add_room_button.grid(row=0, column=2, padx=5)

        self.remove_room_button = tk.Button(self, text="Stop Monitoring", command=self.stop_monitoring)
        self.remove_room_button.grid(row=0, column=3)

        self.monitored_rooms_label = tk.Label(self, text="Monitored Rooms:")
        self.monitored_rooms_label.grid(row=1, column=0, columnspan=4, pady=(10, 5))

        self.monitored_rooms_listbox = tk.Listbox(self, width=50)
        self.monitored_rooms_listbox.grid(row=2, column=0, columnspan=4)

    def start_monitoring(self):
        room_id = self.room_id_entry.get()
        if room_id:
            data = {"room_id": int(room_id)}
            response = requests.post("http://127.0.0.1:8000/add_room", json=data)
            if response.status_code == 200:
                self.monitored_rooms_listbox.insert(tk.END, room_id)
            else:
                messagebox.showerror("Add RoomId Error",response.json()["error"])

    def stop_monitoring(self):
        selected_room = self.monitored_rooms_listbox.curselection()
        if selected_room:
            room_id = self.monitored_rooms_listbox.get(selected_room)
            data = {"room_id": int(room_id)}
            response = requests.post("http://127.0.0.1:8000/remove_room", json=data)
            if response.status_code == 200:
                self.monitored_rooms_listbox.delete(selected_room)
            else:
                messagebox.showerror("Error", response.json()["error"])

def start_gui():
    app = ChatRoomMonitoringGUI()
    app.mainloop()
