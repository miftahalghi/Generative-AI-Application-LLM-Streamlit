"""
bot/database.py
---------------
Thread-safe SQLite connection dan semua operasi CRUD untuk orders.
Tidak ada global cursor/conn — setiap thread mendapat koneksi sendiri.
"""

import sqlite3
import threading
from datetime import datetime, timedelta
import random

DB_PATH = "orders.db"

_local = threading.local()


def get_conn() -> sqlite3.Connection:
    """Mengembalikan koneksi SQLite per-thread (thread-local)."""
    if not hasattr(_local, "conn"):
        _local.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row  # hasil query bisa diakses seperti dict
        _init_schema(_local.conn)
    return _local.conn


def _init_schema(conn: sqlite3.Connection) -> None:
    """Membuat tabel jika belum ada."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT    NOT NULL,
            vehicle_type  TEXT    NOT NULL,
            brand_code    TEXT    NOT NULL,
            model_code    TEXT    NOT NULL,
            year_code     TEXT    NOT NULL,
            order_date    TEXT    NOT NULL,
            delivery_date TEXT    NOT NULL
        )
    """)
    conn.commit()


def insert_order(
    customer_name: str,
    vehicle_type: str,
    brand_code: str,
    model_code: str,
    year_code: str,
) -> dict:
    """
    Menyimpan order baru ke DB.
    Mengembalikan dict berisi data order termasuk estimasi delivery.
    """
    order_date = datetime.now()
    delivery_date = order_date + timedelta(days=random.randint(5, 14))

    conn = get_conn()
    cursor = conn.execute(
        """
        INSERT INTO orders
            (customer_name, vehicle_type, brand_code, model_code, year_code, order_date, delivery_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            customer_name,
            vehicle_type,
            brand_code,
            model_code,
            year_code,
            order_date.isoformat(),
            delivery_date.isoformat(),
        ),
    )
    conn.commit()

    return {
        "id": cursor.lastrowid,
        "customer_name": customer_name,
        "vehicle_type": vehicle_type,
        "brand_code": brand_code,
        "model_code": model_code,
        "year_code": year_code,
        "order_date": order_date.isoformat(),
        "delivery_date": delivery_date.date().isoformat(),
    }


def fetch_all_orders() -> list[dict]:
    """Mengambil semua order dari DB sebagai list of dict."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, customer_name, vehicle_type, brand_code, model_code, year_code, order_date, delivery_date FROM orders"
    ).fetchall()
    return [dict(row) for row in rows]
