from flask import Blueprint, render_template, request, redirect, url_for, session
import sqlite3

admin_bp = Blueprint('admin', __name__)

def connect_db():
    conn = sqlite3.connect('kleidung.db')
    conn.row_factory = sqlite3.Row
    return conn

# Admin Login
@admin_bp.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = connect_db()
        c = conn.cursor()
        c.execute("SELECT * FROM admin WHERE username=? AND password=?", (username, password))
        admin = c.fetchone()
        conn.close()
        if admin:
            session["admin_logged_in"] = True
            return redirect(url_for("admin.admin_dashboard"))
        else:
            return render_template("admin_login.html", error="Falscher Benutzername oder Passwort")
    return render_template("admin_login.html")

# Dashboard
@admin_bp.route("/admin_dashboard")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin.admin_login"))
    conn = connect_db()
    c = conn.cursor()
    c.execute('''
        SELECT b.*, p.name AS produkt_name
        FROM bestellungen b
        JOIN produkte p ON b.produkt_id = p.id
    ''')
    bestellungen = c.fetchall()
    conn.close()
    return render_template("admin_dashboard.html", bestellungen=bestellungen)

# Admin Logout
@admin_bp.route("/admin_logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin.admin_login"))

# Add-Kleidung Seite (GET)
@admin_bp.route("/add_kleidung_page")
def add_kleidung_page():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin.admin_login"))
    return render_template("admin.html")
