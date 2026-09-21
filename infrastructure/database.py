import sqlite3

def init_db():
    conn = sqlite3.connect("ecology.db")
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS eco_points
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    name TEXT NOT NULL, address TEXT, 
                    latitude REAL NOT NULL, 
                    longitude REAL NOT NULL, 
                    wastes TEXT NOT NULL)""")
   
    cursor.execute("""CREATE TABLE IF NOT EXISTS reviews 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    point_id INTEGER NOT NULL, 
                    status TEXT NOT NULL, 
                    created_at TEXT NOT NULL, 
                    FOREIGN KEY (point_id) REFERENCES eco_points (id))""")
    conn.commit()
    conn.close()
