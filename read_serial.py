import serial
import time
from threading import Lock

# ---- CONFIG ----
SERIAL_PORT = "COM3"       # Change to your port
BAUD_RATE = 115200
SERIAL_TIMEOUT = 1         # seconds

# ---- STATE ----
_ser = None
_lock = Lock()

def connect_serial():
    """Open serial connection (singleton)."""
    global _ser
    if _ser is None:
        try:
            _ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=SERIAL_TIMEOUT)
            time.sleep(2)  # ESP32 reset
            print(f"✅ Connected to {SERIAL_PORT}")
        except Exception as e:
            print(f"❌ Failed to open serial port {SERIAL_PORT}: {e}")
            _ser = None
    return _ser

def close_serial():
    """Close serial if open."""
    global _ser
    if _ser is not None and _ser.is_open:
        try:
            _ser.close()
            print("🔌 Serial closed")
        except:
            pass
        _ser = None

def get_latest_reading():
    """
    Read labeled Flex, Accel, Gyro lines from ESP32 and return as dictionary:
    {"flex": [...], "accel": [...], "gyro": [...]}
    """
    ser = connect_serial()
    if not ser:
        return None, "Serial not connected"

    data = {"flex": None, "accel": None, "gyro": None}
    lines_read = 0

    with _lock:
        try:
            while lines_read < 20:  # read up to 20 lines to get all 3
                raw = ser.readline()
                if not raw:
                    continue
                line = raw.decode("utf-8", errors="ignore").strip()
                if not line:
                    continue

                if line.startswith("Flex:"):
                    try:
                        data["flex"] = [float(x) for x in line.split(":")[1].split(",")]
                    except Exception:
                        data["flex"] = None
                elif line.startswith("Accel:"):
                    try:
                        data["accel"] = [float(x) for x in line.split(":")[1].split(",")]
                    except Exception:
                        data["accel"] = None
                elif line.startswith("Gyro:"):
                    try:
                        data["gyro"] = [float(x) for x in line.split(":")[1].split(",")]
                    except Exception:
                        data["gyro"] = None

                if all(v is not None for v in data.values()):
                    return data, None

                lines_read += 1

            return data, "Incomplete reading: some sensors missing"

        except Exception as e:
            return None, f"Serial read error: {e}"
