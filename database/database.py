import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "kernelsense.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def test_connection():
    connection = get_connection()

    try:
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        return result[0] == 1
    finally:
        connection.close()


def create_tables():
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS command_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command TEXT NOT NULL,
                risk TEXT,
                status TEXT,
                output TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS health_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cpu_usage REAL,
                memory_usage REAL,
                disk_usage REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        connection.commit()

    finally:
        connection.close()


def save_command(command, risk, status, output):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO command_history
            (command, risk, status, output)
            VALUES (?, ?, ?, ?)
        """, (command, risk, status, output))

        connection.commit()

        return cursor.lastrowid

    finally:
        connection.close()


def get_command_history(limit=50):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT *
            FROM command_history
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))

        return [dict(row) for row in cursor.fetchall()]

    finally:
        connection.close()


def save_health(cpu_usage, memory_usage, disk_usage):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO health_history
            (cpu_usage, memory_usage, disk_usage)
            VALUES (?, ?, ?)
        """, (cpu_usage, memory_usage, disk_usage))

        connection.commit()

        return cursor.lastrowid

    finally:
        connection.close()


def get_health_history(limit=50):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT *
            FROM health_history
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))

        return [dict(row) for row in cursor.fetchall()]

    finally:
        connection.close()
def save_current_health():
    from linux.cpu import get_cpu_usage
    from linux.memory import get_memory_info
    from linux.storage import get_root_disk_usage

    cpu = get_cpu_usage()
    memory = get_memory_info()
    disk = get_root_disk_usage()

    return save_health(
        cpu_usage=cpu,
        memory_usage=memory["usage_percent"],
        disk_usage=disk["usage_percent"]
    )
