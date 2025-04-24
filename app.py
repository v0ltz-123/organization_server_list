import os  # built-in Python library

from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import check_password_hash
import psycopg2
from dotenv import load_dotenv

app = Flask(__name__)

app.secret_key = 'fovd#BD^2OYvj!a2NUnAvvWAjwNL%$KRuNcrxL8uave4v0YePf$JlMbBWO#I&b#f'  # <<< Add a strong random string here

# Hashed Admin password (the hash you generated)
ADMIN_PASSWORD_HASH = 'scrypt:32768:8:1$Tal9Kqn3VUUMB7dn$74d887280c2bc69582109450391bf89f6799929f9aa224c166d7a99221d39021c8294c145c5486e24d5d2d234762ded96d2f0eafe3c819b98f17953dc2d13964'


# Connect to your PostgreSQL database
def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    return conn

# --- HOME PAGE ROUTE ---
@app.route('/', methods=['GET', 'POST'])
def index():
    conn = get_db_connection()
    cur = conn.cursor()

    search_query = request.args.get('q')
    if search_query:
        cur.execute("""
            SELECT * FROM organizations
            WHERE organization ILIKE %s
            OR cms ILIKE %s
            OR server ILIKE %s
            OR remote_type ILIKE %s
            OR notes ILIKE %s
        """, tuple('%' + search_query + '%' for _ in range(5)))
    else:
        cur.execute("""
        SELECT * FROM organizations
        ORDER BY id DESC
        LIMIT 10
    """)
    organizations = cur.fetchall()
    
    cur.close()
    conn.close()
    return render_template('index.html', organizations=organizations)


# --- ADD DATA ROUTE ---
@app.route('/add', methods=['POST'])
def add_organization():
     #New admin check
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    organization = request.form['organization']
    cms = request.form['cms']
    server = request.form['server']
    remote_type = request.form['remote_type']
    notes = request.form['notes']

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO organizations (organization, cms, server, remote_type, notes)
        VALUES (%s, %s, %s, %s, %s)
    """, (organization, cms, server, remote_type, notes))
    conn.commit()
    cur.close()
    conn.close()
    return redirect('/')

# --- ADMIN LOGIN PAGE ---
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form['password']
        if check_password_hash(ADMIN_PASSWORD_HASH, password):
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error="Incorrect password")
    return render_template('admin_login.html')

# --- ADMIN DASHBOARD PAGE ---
@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM organizations
        ORDER BY id DESC
        LIMIT 10
    """)
    organizations = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('admin_dashboard.html', organizations=organizations)


# --- ADMIN LOGOUT PAGE ---
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect('/')

# --- ADD ORGANIZATION PAGE ---
@app.route('/admin/add-organization', methods=['GET', 'POST'])
def add_organization_admin():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        organization = request.form['organization']
        cms = request.form['cms']
        server = request.form['server']
        remote_type = request.form['remote_type']
        notes = request.form['notes']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO organizations (organization, cms, server, remote_type, notes)
            VALUES (%s, %s, %s, %s, %s)
        """, (organization, cms, server, remote_type, notes))
        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for('admin_dashboard'))
    
    return render_template('add_organization.html')


if __name__ == '__main__':
    app.run(debug=True)
