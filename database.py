import sqlite3

class Kleidung:
    def __init__(self, name, preis, grosse, farbe, bild_path):
        self.name = name
        self.preis = preis
        self.grosse = grosse
        self.farbe = farbe
        self.bild_path = bild_path

class Database:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.c = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.c.execute('''
        CREATE TABLE IF NOT EXISTS kleidung (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            preis REAL,
            grosse TEXT,
            farbe TEXT,
            bild_path TEXT
        )
        ''')
        self.conn.commit()

    def add_kleidung(self, kleidung):
        self.c.execute('''
        INSERT INTO kleidung (name, preis, grosse, farbe, bild_path)
        VALUES (?, ?, ?, ?, ?)
        ''', (kleidung.name, kleidung.preis, kleidung.grosse, kleidung.farbe, kleidung.bild_path))
        self.conn.commit()

    def get_all(self):
        self.c.execute("SELECT * FROM kleidung")
        return self.c.fetchall()

    def get_by_id(self, id):
        self.c.execute("SELECT * FROM kleidung WHERE id=?", (id,))
        return self.c.fetchone()
