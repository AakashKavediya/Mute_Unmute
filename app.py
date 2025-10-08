from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import csv
import os

import read_serial

app = FastAPI(title="ESP32 Serial API")

# ----------------------
# CORS (adjust as needed)
# ----------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins or replace with your frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------
# CSV setup
# ----------------------
CSV_FILE = "dataset.csv"
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "timestamp",
            "flex1","flex2","flex3","flex4","flex5",
            "accelX","accelY","accelZ",
            "gyroX","gyroY","gyroZ"
        ])

# ----------------------
# Shutdown event
# ----------------------
@app.on_event("shutdown")
def shutdown_event():
    read_serial.close_serial()

# ----------------------
# Routes
# ----------------------
@app.get("/")
def root():
    return {"message": "FastAPI ESP32 bridge. GET /read or /save"}

@app.get("/read")
def read_once():
    """Return latest reading from ESP32 (no file write)."""
    readings, err = read_serial.get_latest_reading()
    if err:
        return JSONResponse({"error": err}, status_code=500)
    return {"data": readings}

@app.get("/save")
def read_and_save():
    """Read from ESP32 and append one row to CSV (timestamp + readings)."""
    readings, err = read_serial.get_latest_reading()
    if err:
        return JSONResponse({"error": err}, status_code=500)

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(CSV_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            row = [ts] + readings["flex"] + readings["accel"] + readings["gyro"]
            writer.writerow(row)
    except Exception as e:
        return JSONResponse({"error": f"Failed to write CSV: {e}"}, status_code=500)

    return {"message": "saved", "timestamp": ts, "data": readings}
