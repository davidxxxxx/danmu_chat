import multiprocessing
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from data_collector import data_collector
from live_plotter import live_plotter

app = FastAPI()

# Data model for adding a room
class AddRoomInput(BaseModel):
    room_id: int

# Data model for removing a room
class RemoveRoomInput(BaseModel):
    room_id: int

# A dictionary to store the data_collector and live_plotter processes for each room
room_processes = {}

# Global variable to store the db_queue
db_queue = None

@app.post("/add_room")
async def add_room(input_data: AddRoomInput):
    room_id = input_data.room_id

    if room_id in room_processes:
        return JSONResponse(content={"error": f"Room {room_id} is already being monitored"}, status_code=400)

    # Start data_collector and live_plotter processes for the given room_id
    data_collector_process = multiprocessing.Process(target=data_collector, args=(room_id, db_queue))
    live_plotter_process = multiprocessing.Process(target=live_plotter, args=(room_id,db_queue))

    data_collector_process.start()
    live_plotter_process.start()

    room_processes[room_id] = {
        "data_collector": data_collector_process,
        "live_plotter": live_plotter_process
    }

    return {"status": "success", "message": f"Started monitoring room {room_id}"}

@app.post("/remove_room")
async def remove_room(input_data: RemoveRoomInput):
    room_id = input_data.room_id

    if room_id not in room_processes:
        return JSONResponse(content={"error": f"Room {room_id} is not being monitored"}, status_code=400)

    # Terminate data_collector and live_plotter processes for the given room_id
    room_processes[room_id]["data_collector"].terminate()
    room_processes[room_id]["live_plotter"].terminate()

    del room_processes[room_id]

    return {"status": "success", "message": f"Stopped monitoring room {room_id}"}

def start_backend(queue):
    global db_queue
    db_queue = queue
    import uvicorn
    uvicorn.run("backend:app", host="127.0.0.1", port=8000, log_level="info")
