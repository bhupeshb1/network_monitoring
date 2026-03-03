import sqlite3
from scapy.all import sniff, IP
from datetime import datetime

DB_FILE = "traffic.db"


def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address TEXT UNIQUE,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS traffic_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER,
            bytes_transferred INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (device_id) REFERENCES devices (id)
        )
    """)

    conn.commit()
    conn.close()


def get_or_create_device(ip):
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT id FROM devices WHERE ip_address = ?", (ip,))
    row = c.fetchone()

    if row:
        device_id = row["id"]
    else:
        c.execute("INSERT INTO devices (ip_address) VALUES (?)", (ip,))
        conn.commit()
        device_id = c.lastrowid

    conn.close()
    return device_id


def insert_traffic(device_id, byte_count):
    conn = get_connection()
    c = conn.cursor()

    c.execute(
        "INSERT INTO traffic_logs (device_id, bytes_transferred) VALUES (?, ?)",
        (device_id, byte_count),
    )

    conn.commit()
    conn.close()


def process_packet(packet):
    if IP in packet:
        src_ip = packet[IP].src
        packet_size = len(packet)

        device_id = get_or_create_device(src_ip)
        insert_traffic(device_id, packet_size)

        print(f"{datetime.now()} | {src_ip} | {packet_size} bytes")


def start_sniffing():
    print("Starting packet capture...")
    sniff(prn=process_packet, store=False)


if __name__ == "__main__":
    init_db()
    start_sniffing()
