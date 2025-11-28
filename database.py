import sqlite3
from datetime import datetime

import cv2
import numpy as np

DB_PATH = "snapshots.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            image BLOB NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()
    print("Successively initialized database.")


def save_image_to_db(img_bgr: np.ndarray):
    # encode as PNG bytes
    ok, buf = cv2.imencode(".png", img_bgr)
    if not ok:
        print("Could not save image.")
        return

    data = buf.tobytes()
    date = datetime.now()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO snapshots (created_at, image) VALUES (?, ?)",
        (date, data),
    )
    conn.commit()
    conn.close()

    print("Successively saved image to database.")


def load_images_from_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT created_at, image FROM snapshots ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return rows
