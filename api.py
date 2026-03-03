# api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
from datetime import datetime
from typing import List

DB_FILE = "traffic.db"
app = FastAPI(title="Raspberry Pi Network Monitoring API")


# ----------------------------
# Pydantic models
# ----------------------------
class Device(BaseModel):
    id: int
    ip_address: str
    first_seen: str


class TrafficLog(BaseModel):
    id: int
    device_id: int
    bytes_transferred: int
    timestamp: str


# ----------------------------
# Helper: DB connection
# ----------------------------
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


# ----------------------------
# Endpoints
# ----------------------------
@app.get("/devices", response_model=List[Device])
def get_devices():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM devices")
    rows = c.fetchall()
    conn.close()
    return [Device(**dict(row)) for row in rows]


@app.get("/devices/{device_id}", response_model=Device)
def get_device(device_id: int):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM devices WHERE id = ?", (device_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return Device(**dict(row))
    else:
        raise HTTPException(status_code=404, detail="Device not found")


@app.get("/devices/{device_id}/traffic", response_model=List[TrafficLog])
def get_device_traffic(device_id: int):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM traffic_logs WHERE device_id = ?", (device_id,))
    rows = c.fetchall()
    conn.close()
    return [TrafficLog(**dict(row)) for row in rows]


@app.get("/traffic/recent", response_model=List[TrafficLog])
def get_recent_traffic(limit: int = 50):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM traffic_logs ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return [TrafficLog(**dict(row)) for row in rows]


@app.get("/stats/top", response_model=List[dict])
def get_top_devices(limit: int = 5):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        SELECT d.ip_address, SUM(t.bytes_transferred) as total_bytes
        FROM devices d
        JOIN traffic_logs t ON d.id = t.device_id
        GROUP BY d.id
        ORDER BY total_bytes DESC
        LIMIT ?
    """, (limit,))
    rows = c.fetchall()
    conn.close()
    return [{"ip_address": row["ip_address"], "total_bytes": row["total_bytes"]} for row in rows]
