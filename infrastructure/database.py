import sqlite3

def init_db():
    conn = sqlite3.connect('ecology.db')
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS eco_points (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        address TEXT,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        wastes TEXT NOT NULL,
        owner_name TEXT DEFAULT 'БЕЛВТОРРЕСУРСЫ'
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        point_id INTEGER NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (point_id) REFERENCES eco_points (id)
    )
    """)

    # НОВОЕ: справочник владельцев
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS owners (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        is_active INTEGER NOT NULL DEFAULT 1
    )
    """)

    # Начальное заполнение (один раз, если пусто)
    cursor.execute("SELECT COUNT(*) FROM owners")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO owners (name, password) VALUES (?, ?)",
            [
                ('БЕЛВТОРРЕСУРСЫ', 'bel123'),
                ('ЭКОЛАЙН',        'line123'),
                ('БЕЛВТОРЧЕРМЕТ',  'chermet123'),
            ],
        )

    conn.commit()
    conn.close()