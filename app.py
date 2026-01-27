import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
from admin import admin_bp

app = Flask(__name__)
app.secret_key = "mein_geheimer_schluessel"
app.register_blueprint(admin_bp)

# Upload-Ordner
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'images')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Datenbankverbindung
def connect_db():
    conn = sqlite3.connect('kleidung.db')
    conn.row_factory = sqlite3.Row
    return conn

# Tabellen erstellen
def create_tables():
    conn = connect_db()
    c = conn.cursor()
    # Produkte
    c.execute('''
        CREATE TABLE IF NOT EXISTS produkte (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            preis REAL,
            grosse TEXT,
            farbe TEXT,
            bild TEXT,
            kategorie TEXT
        )
    ''')
    # Bestellungen
    c.execute('''
        CREATE TABLE IF NOT EXISTS bestellungen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produkt_id INTEGER,
            vorname TEXT,
            nachname TEXT,
            rufnummer TEXT,
            adresse TEXT,
            bank TEXT,
            menge INTEGER,
            farbe TEXT,
            grosse TEXT,
            gesamtpreis REAL
        )
    ''')
    conn.commit()
    conn.close()

create_tables()

# ---------- Home / Suche ----------
@app.route('/', methods=['GET', 'POST'])
def home():
    conn = connect_db()
    c = conn.cursor()

    if request.method == 'POST':
        search = request.form.get('search', '').strip()
        c.execute("SELECT * FROM produkte WHERE name LIKE ?", ('%'+search+'%',))
        produkte = c.fetchall()
        conn.close()
        return render_template('search_results.html', produkte=produkte, query=search)

    c.execute("SELECT kategorie, MIN(bild) AS bild FROM produkte GROUP BY kategorie")
    kategorien = c.fetchall()
    conn.close()
    return render_template('index.html', kategorien=kategorien)

# Kategorie-Seite
@app.route('/kategorie/<kategorie_name>')
def kategorie(kategorie_name):
    conn = connect_db()
    c = conn.cursor()
    c.execute("SELECT * FROM produkte WHERE kategorie=?", (kategorie_name,))
    produkte = c.fetchall()
    conn.close()
    return render_template('produkte.html', produkte=produkte, kategorie_name=kategorie_name)

# Produktdetailseite
@app.route('/produkt/<int:produkt_id>')
def detail(produkt_id):
    conn = connect_db()
    c = conn.cursor()
    c.execute("SELECT * FROM produkte WHERE id=?", (produkt_id,))
    produkt = c.fetchone()
    conn.close()
    if not produkt:
        return "Produkt nicht gefunden", 404
    return render_template('detail.html', produkt=produkt)

# Kundendaten Formular
@app.route('/bestellungen_info/<int:produkt_id>', methods=['POST'])
def bestellungen_info(produkt_id):
    menge = int(request.form['menge'])
    grosse = request.form['grosse']
    farbe = request.form['farbe']

    conn = connect_db()
    c = conn.cursor()
    c.execute("SELECT * FROM produkte WHERE id=?", (produkt_id,))
    produkt = c.fetchone()
    conn.close()
    if not produkt:
        return "Produkt nicht gefunden", 404

    gesamtpreis = produkt['preis'] * menge
    return render_template('bestellung_info.html', produkt=produkt,
                           menge=menge, grosse=grosse, farbe=farbe,
                           gesamtpreis=gesamtpreis)

# Bestellung absenden
@app.route('/bestllung_abschicken/<int:produkt_id>', methods=['POST'])
def bestllung_abschicken(produkt_id):
    vorname = request.form['vorname']
    nachname = request.form['nachname']
    rufnummer = request.form['rufnummer']
    adresse = request.form['adresse']
    bank = request.form['bank']
    menge = int(request.form['menge'])
    farbe = request.form['farbe']
    grosse = request.form['grosse']
    gesamtpreis = float(request.form['gesamtpreis'])

    conn = connect_db()
    c = conn.cursor()
    c.execute('''
        INSERT INTO bestellungen 
        (produkt_id, vorname, nachname, rufnummer, adresse, bank, menge, farbe, grosse, gesamtpreis)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (produkt_id, vorname, nachname, rufnummer, adresse, bank, menge, farbe, grosse, gesamtpreis))
    conn.commit()
    conn.close()
    return render_template('danke.html', vorname=vorname, gesamtpreis=gesamtpreis)

# Edit Produkt
@app.route('/edit_produkt/<int:produkt_id>', methods=['GET', 'POST'])
def edit_produkt(produkt_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.admin_login'))
    conn = connect_db()
    c = conn.cursor()
    c.execute("SELECT * FROM produkte WHERE id=?", (produkt_id,))
    produkt = c.fetchone()

    if request.method == 'POST':
        name = request.form['name']
        preis = request.form['preis']
        grosse = request.form['grosse']
        farbe = request.form['farbe']
        kategorie = request.form['kategorie']
        bild_datei = request.files.get('bild')
        filename = produkt['bild']

        if bild_datei and bild_datei.filename:
            filename = secure_filename(bild_datei.filename)
            folder = os.path.join(app.config['UPLOAD_FOLDER'], kategorie)
            os.makedirs(folder, exist_ok=True)
            bild_datei.save(os.path.join(folder, filename))

        c.execute('''
            UPDATE produkte SET name=?, preis=?, grosse=?, farbe=?, bild=?, kategorie=? WHERE id=?
        ''', (name, preis, grosse, farbe, filename, kategorie, produkt_id))
        conn.commit()
        conn.close()
        return redirect(url_for('detail', produkt_id=produkt_id))

    conn.close()
    return render_template('edit_produkt.html', produkt=produkt)

# Delete Produkt
@app.route('/delete_produkt/<int:produkt_id>', methods=['POST'])
def delete_produkt(produkt_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.admin_login'))
    conn = connect_db()
    c = conn.cursor()
    c.execute("DELETE FROM produkte WHERE id=?", (produkt_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('home'))

# Neues Produkt hinzufügen (POST)
@app.route('/add_kleidung', methods=['GET', 'POST'])
def add_kleidung():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.admin_login'))

    if request.method == 'POST':
        # Daten aus dem Formular
        name = request.form['name']
        preis = request.form['preis']
        grosse = request.form['grosse']
        farbe = request.form['farbe']
        kategorie = request.form['kategorie']
        bild_datei = request.files.get('bild')

        filename = "default.jpg"
        if bild_datei and bild_datei.filename:
            filename = secure_filename(bild_datei.filename)
            folder = os.path.join(app.config['UPLOAD_FOLDER'], kategorie)
            os.makedirs(folder, exist_ok=True)
            bild_datei.save(os.path.join(folder, filename))

        # In DB speichern
        conn = connect_db()
        c = conn.cursor()
        c.execute('''
            INSERT INTO produkte (name, preis, grosse, farbe, bild, kategorie)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, preis, grosse, farbe, filename, kategorie))
        conn.commit()
        conn.close()

        return redirect(url_for('home'))

    # GET-Request → Formular anzeigen
    return render_template('admin.html')


if __name__ == "__main__":
    app.run(debug=True)
