from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_file
import sqlite3
import os
import glob
import shutil
import socket
from datetime import datetime, date
import json
import sys

app = Flask(__name__)
app.secret_key = 'barbershop_secret_2024'

# Use BARBERSHOP_DATA if provided (for packaged app), else fallback to current directory
DATA_DIR = os.getenv('BARBERSHOP_DATA', os.path.dirname(__file__))
DB_PATH = os.path.join(DATA_DIR, 'barbershop.db')
STATIC_ROOT = os.path.dirname(__file__) # Static files (templates/css) remain in script dir

# ── Database Setup ────────────────────────────────────────────────────────────

@app.route('/icon.png')
def get_icon():
    # Serve custom uploaded logo if exists from DATA_DIR, otherwise default icon.png from STATIC_ROOT
    uploads_dir = os.path.join(DATA_DIR, 'static', 'uploads')
    for ext in ['png', 'jpg', 'jpeg', 'webp', 'svg']:
        logo_path = os.path.join(uploads_dir, f'logo.{ext}')
        if os.path.exists(logo_path):
            return send_file(logo_path)
    return send_file(os.path.join(STATIC_ROOT, 'AlShahidLogo.jpeg'))

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('8.8.8.8', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def init_db():
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS workers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            pin TEXT NOT NULL,
            role TEXT DEFAULT 'barber',
            phone TEXT,
            email TEXT,
            address TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now'))
        );
        -- ensure legacy installations gain new columns if missing

        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            duration_minutes INTEGER DEFAULT 30,
            is_active INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id INTEGER,
            customer_name TEXT DEFAULT 'Walk-in',
            service_id INTEGER,
            custom_service TEXT,
            price REAL NOT NULL,
            status TEXT DEFAULT 'completed',
            payment_method TEXT DEFAULT 'cash',
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY(worker_id) REFERENCES workers(id),
            FOREIGN KEY(service_id) REFERENCES services(id)
        );

        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT DEFAULT 'other',
            added_by INTEGER,
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY(added_by) REFERENCES workers(id)
        );

        CREATE TABLE IF NOT EXISTS payouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id INTEGER,
            amount REAL NOT NULL,
            period TEXT,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY(worker_id) REFERENCES workers(id)
        );

        CREATE TABLE IF NOT EXISTS shop_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );

        INSERT OR IGNORE INTO shop_settings VALUES ('shop_name', 'Classic Cuts Barbershop');
        INSERT OR IGNORE INTO shop_settings VALUES ('currency', 'Rs');
        INSERT OR IGNORE INTO shop_settings VALUES ('admin_pin', '1234');
        INSERT OR IGNORE INTO shop_settings VALUES ('worker_commission', '30');

        INSERT OR IGNORE INTO workers (id, name, pin, role) VALUES (1, 'Admin', '1234', 'admin');

        INSERT OR IGNORE INTO services (id, name, price, duration_minutes) VALUES
            (1, 'Haircut', 300, 20),
            (2, 'Shave', 150, 15),
            (3, 'Haircut + Shave', 400, 35),
            (4, 'Hair Wash', 100, 10),
            (5, 'Beard Trim', 200, 15),
            (6, 'Head Massage', 150, 20),
            (7, 'Facial', 500, 30),
            (8, 'Kids Haircut', 200, 15);
        """)

    # after creating tables, ensure that workers table has newer columns (for upgrades)
    # perform migration checks outside of script because ALTER within execscript
    # may not support conditional logic easily.
    cols = [r['name'] for r in db.execute("PRAGMA table_info(workers)").fetchall()]
    for col, coltype in [('phone','TEXT'), ('email','TEXT'), ('address','TEXT')]:
        if col not in cols:
            db.execute(f"ALTER TABLE workers ADD COLUMN {col} {coltype}")

init_db()

# ── Helpers ───────────────────────────────────────────────────────────────────

def get_setting(key):
    with get_db() as db:
        row = db.execute("SELECT value FROM shop_settings WHERE key=?", (key,)).fetchone()
        return row['value'] if row else ''

def query(sql, args=(), one=False):
    with get_db() as db:
        cur = db.execute(sql, args)
        rv = cur.fetchall()
        return (rv[0] if rv else None) if one else rv

def execute(sql, args=()):
    with get_db() as db:
        cur = db.execute(sql, args)
        db.commit()
        return cur.lastrowid

# ── Auth ──────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        pin = request.form.get('pin', '')
        worker = query("SELECT * FROM workers WHERE pin=? AND is_active=1", (pin,), one=True)
        if worker:
            session['worker_id'] = worker['id']
            session['worker_name'] = worker['name']
            session['worker_role'] = worker['role']
            if worker['role'] == 'admin':
                return redirect(url_for('dashboard'))
            return redirect(url_for('worker_dashboard'))
        return render_template('login.html', error='Invalid PIN', shop_name=get_setting('shop_name'))
    return render_template('login.html', shop_name=get_setting('shop_name'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'worker_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('worker_role') != 'admin':
            return redirect(url_for('worker_dashboard'))
        return f(*args, **kwargs)
    return decorated

# ── Worker Dashboard ──────────────────────────────────────────────────────────

@app.route('/worker')
@login_required
def worker_dashboard():
    worker_id = session['worker_id']
    from_date = request.args.get('from', date.today().isoformat())
    to_date = request.args.get('to', date.today().isoformat())

    today_jobs = query("""
        SELECT a.*, s.name as service_name
        FROM appointments a
        LEFT JOIN services s ON a.service_id = s.id
        WHERE a.worker_id=? AND date(a.created_at) BETWEEN ? AND ?
        ORDER BY a.created_at DESC
    """, (worker_id, from_date, to_date))

    today_earnings = sum(j['price'] for j in today_jobs)
    today_count = len(today_jobs)

    services = query("SELECT * FROM services WHERE is_active=1 ORDER BY name")
    currency = get_setting('currency')
    shop_name = get_setting('shop_name')
    commission = int(get_setting('worker_commission') or 30)

    return render_template('worker.html',
        worker_name=session['worker_name'],
        worker_role=session['worker_role'],
        today_jobs=today_jobs,
        today_earnings=today_earnings,
        today_count=today_count,
        services=services,
        currency=currency,
        shop_name=shop_name,
        today=date.today().isoformat(),
        from_date=from_date,
        to_date=to_date,
        commission=commission
    )

@app.route('/api/add_job', methods=['POST'])
@login_required
def add_job():
    data = request.json
    worker_id = session['worker_id']

    service_id = data.get('service_id')
    custom_service = data.get('custom_service', '')
    price = float(data.get('price', 0))
    customer = data.get('customer_name', 'Walk-in') or 'Walk-in'
    payment = data.get('payment_method', 'cash')
    notes = data.get('notes', '')

    if price <= 0:
        return jsonify({'success': False, 'error': 'Price must be greater than 0'})

    job_id = execute("""
        INSERT INTO appointments (worker_id, customer_name, service_id, custom_service, price, payment_method, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (worker_id, customer, service_id or None, custom_service, price, payment, notes))

    return jsonify({'success': True, 'job_id': job_id})

@app.route('/api/delete_job/<int:job_id>', methods=['DELETE'])
@login_required
def delete_job(job_id):
    # Workers can only delete their own jobs from today
    worker_id = session['worker_id']
    today = date.today().isoformat()
    job = query("SELECT * FROM appointments WHERE id=? AND worker_id=? AND date(created_at)=?",
                (job_id, worker_id, today), one=True)
    if not job:
        return jsonify({'success': False, 'error': 'Not found or not allowed'})
    execute("DELETE FROM appointments WHERE id=?", (job_id,))
    return jsonify({'success': True})

@app.route('/api/worker/profile', methods=['GET'])
@login_required
def worker_profile():
    worker_id = session['worker_id']
    worker = query("SELECT id, name, pin, role, phone, email, address FROM workers WHERE id=?", (worker_id,), one=True)
    if not worker:
        return jsonify({'success': False, 'error': 'Worker not found'})
    return jsonify({'success': True, 'worker': dict(worker)})


@app.route('/api/worker/profile', methods=['POST'])
@login_required
def update_worker_profile():
    worker_id = session['worker_id']
    data = request.json or {}
    # fetch current
    cur = query("SELECT * FROM workers WHERE id=?", (worker_id,), one=True)
    if not cur:
        return jsonify({'success': False, 'error': 'Worker not found'})
    name = data.get('name', cur['name'])
    phone = data.get('phone', cur.get('phone', '') if isinstance(cur, dict) else cur['phone'])
    email = data.get('email', cur.get('email', '') if isinstance(cur, dict) else cur['email'])
    address = data.get('address', cur.get('address', '') if isinstance(cur, dict) else cur['address'])
    execute("UPDATE workers SET name=?, phone=?, email=?, address=? WHERE id=?", (name, phone, email, address, worker_id))
    worker = query("SELECT id, name, role, phone, email, address FROM workers WHERE id=?", (worker_id,), one=True)
    return jsonify({'success': True, 'worker': dict(worker)})

@app.route('/api/worker/change-pin', methods=['POST'])
@login_required
def change_pin():
    data = request.json
    worker_id = session['worker_id']
    current_pin = data.get('current_pin', '').strip()
    new_pin = data.get('new_pin', '').strip()
    confirm_pin = data.get('confirm_pin', '').strip()

    if not current_pin or not new_pin or not confirm_pin:
        return jsonify({'success': False, 'error': 'All fields are required'})

    # Verify current PIN
    worker = query("SELECT * FROM workers WHERE id=? AND pin=?", (worker_id, current_pin), one=True)
    if not worker:
        return jsonify({'success': False, 'error': 'Current PIN is incorrect'})

    # Check new PIN matches confirmation
    if new_pin != confirm_pin:
        return jsonify({'success': False, 'error': 'New PIN and confirmation do not match'})

    # Check PIN length
    if len(new_pin) < 4:
        return jsonify({'success': False, 'error': 'PIN must be at least 4 digits'})

    # Check if PIN is already in use by another worker
    existing = query("SELECT id FROM workers WHERE pin=? AND id!=? AND is_active=1", (new_pin, worker_id), one=True)
    if existing:
        return jsonify({'success': False, 'error': 'PIN already in use by another worker'})

    # Update PIN
    execute("UPDATE workers SET pin=? WHERE id=?", (new_pin, worker_id))
    return jsonify({'success': True, 'message': 'PIN changed successfully'})

@app.route('/api/worker/stats', methods=['GET'])
@login_required
def worker_stats():
    worker_id = session['worker_id']
    period = request.args.get('period', 'today')  # today, week, month
    
    from datetime import timedelta
    today = date.today()
    
    if period == 'today':
        start_date = today.isoformat()
        end_date = today.isoformat()
    elif period == 'week':
        start_date = (today - timedelta(days=7)).isoformat()
        end_date = today.isoformat()
    elif period == 'month':
        start_date = (today - timedelta(days=30)).isoformat()
        end_date = today.isoformat()
    else:
        start_date = today.isoformat()
        end_date = today.isoformat()

    # Get worker earnings
    earnings_data = query("""
        SELECT SUM(price) as total, COUNT(*) as jobs, 
               AVG(price) as avg_price
        FROM appointments
        WHERE worker_id=? AND date(created_at) BETWEEN ? AND ?
    """, (worker_id, start_date, end_date), one=True)

    # Get payment method breakdown
    payment_breakdown = query("""
        SELECT payment_method, COUNT(*) as count, SUM(price) as total
        FROM appointments
        WHERE worker_id=? AND date(created_at) BETWEEN ? AND ?
        GROUP BY payment_method
    """, (worker_id, start_date, end_date))

    return jsonify({
        'success': True,
        'total_earnings': earnings_data['total'] or 0,
        'total_jobs': earnings_data['jobs'] or 0,
        'avg_price': round(earnings_data['avg_price'] or 0, 2),
        'payment_breakdown': [dict(p) for p in payment_breakdown]
    })

@app.route('/api/worker/payouts', methods=['GET', 'POST'])
@login_required
def worker_payouts():
    worker_id = session['worker_id']
    if request.method == 'POST':
        data = request.json
        amount = float(data.get('amount', 0))
        period = data.get('period', 'daily')
        notes = data.get('notes', '')
        if amount <= 0:
            return jsonify({'success': False, 'error': 'Amount must be greater than 0'})
        pid = execute("INSERT INTO payouts (worker_id, amount, period, notes) VALUES (?,?,?,?)",
                      (worker_id, amount, period, notes))
        return jsonify({'success': True, 'id': pid})
    
    payouts = query("SELECT * FROM payouts WHERE worker_id=? ORDER BY created_at DESC", (worker_id,))
    return jsonify({'success': True, 'payouts': [dict(p) for p in payouts]})

# ── Admin Dashboard ───────────────────────────────────────────────────────────

@app.route('/dashboard')
@login_required
@admin_required
def dashboard():
    from_date = request.args.get('from', date.today().isoformat())
    to_date = request.args.get('to', date.today().isoformat())
    currency = get_setting('currency')
    shop_name = get_setting('shop_name')

    # Status stats (for the selected range)
    today_jobs = query("""
        SELECT a.*, w.name as worker_name, s.name as service_name
        FROM appointments a
        LEFT JOIN workers w ON a.worker_id = w.id
        LEFT JOIN services s ON a.service_id = s.id
        WHERE date(a.created_at) BETWEEN ? AND ?
        ORDER BY a.created_at DESC
    """, (from_date, to_date))

    today_revenue = sum(j['price'] for j in today_jobs)
    today_count = len(today_jobs)

    # Per-worker stats (include admin if they have jobs)
    worker_stats = query("""
        SELECT w.name, COUNT(a.id) as jobs, SUM(a.price) as earnings
        FROM workers w
        LEFT JOIN appointments a ON w.id=a.worker_id AND date(a.created_at) BETWEEN ? AND ?
        WHERE w.is_active=1
        GROUP BY w.id, w.name
        HAVING earnings > 0 OR w.role='barber'
        ORDER BY earnings DESC NULLS LAST
    """, (from_date, to_date))

    # Expenses (for the selected range)
    today_expenses = query("""
        SELECT e.*, w.name as added_by_name
        FROM expenses e
        LEFT JOIN workers w ON e.added_by=w.id
        WHERE date(e.created_at) BETWEEN ? AND ?
        ORDER BY e.created_at DESC
    """, (from_date, to_date))
    today_expense_total = sum(e['amount'] for e in today_expenses)
    
    # Payouts (for the selected range)
    today_payouts = query("SELECT SUM(amount) as total FROM payouts WHERE date(created_at) BETWEEN ? AND ?", (from_date, to_date), one=True)
    today_payout_total = today_payouts['total'] or 0
    today_net = today_revenue - today_expense_total - today_payout_total

    workers = query("SELECT * FROM workers WHERE is_active=1 AND role='barber'")
    services = query("SELECT * FROM services WHERE is_active=1 ORDER BY name")
    commission = int(get_setting('worker_commission') or 30)

    # Get local IP for mobile access display
    local_ip = get_local_ip()

    return render_template('dashboard.html',
        shop_name=shop_name,
        currency=currency,
        today=date.today().isoformat(),
        from_date=from_date,
        to_date=to_date,
        today_jobs=today_jobs,
        today_revenue=today_revenue,
        today_count=today_count,
        worker_stats=worker_stats,
        today_expenses=today_expenses,
        today_expense_total=today_expense_total,
        today_payout_total=today_payout_total,
        today_net=today_net,
        workers=workers,
        services=services,
        local_ip=local_ip,
        commission=commission
    )

# ── Admin APIs ────────────────────────────────────────────────────────────────

@app.route('/api/report')
@login_required
@admin_required
def report():
    start = request.args.get('start', date.today().isoformat())
    end = request.args.get('end', date.today().isoformat())
    currency = get_setting('currency')

    jobs = query("""
        SELECT a.*, w.name as worker_name, s.name as service_name
        FROM appointments a
        LEFT JOIN workers w ON a.worker_id=w.id
        LEFT JOIN services s ON a.service_id=s.id
        WHERE date(a.created_at) BETWEEN ? AND ?
        ORDER BY a.created_at DESC
    """, (start, end))

    expenses = query("""
        SELECT e.*, w.name as added_by_name
        FROM expenses e LEFT JOIN workers w ON e.added_by=w.id
        WHERE date(e.created_at) BETWEEN ? AND ?
        ORDER BY e.created_at DESC
    """, (start, end))

    worker_summary = query("""
        SELECT w.name, COUNT(a.id) as jobs, SUM(a.price) as earnings
        FROM workers w
        LEFT JOIN appointments a ON w.id=a.worker_id AND date(a.created_at) BETWEEN ? AND ?
        WHERE w.role='barber'
        GROUP BY w.id, w.name
        ORDER BY earnings DESC NULLS LAST
    """, (start, end))

    revenue = sum(j['price'] for j in jobs)
    expense_total = sum(e['amount'] for e in expenses)

    payouts = query("""
        SELECT p.*, w.name as worker_name
        FROM payouts p
        LEFT JOIN workers w ON p.worker_id=w.id
        WHERE date(p.created_at) BETWEEN ? AND ?
        ORDER BY p.created_at DESC
    """, (start, end))

    payout_total = sum(p['amount'] for p in payouts)

    return jsonify({
        'jobs': [dict(j) for j in jobs],
        'expenses': [dict(e) for e in expenses],
        'payouts': [dict(p) for p in payouts],
        'worker_summary': [dict(w) for w in worker_summary],
        'revenue': revenue,
        'expense_total': expense_total,
        'payout_total': payout_total,
        'net': revenue - expense_total - payout_total,
        'currency': currency
    })

@app.route('/api/workers', methods=['GET', 'POST'])
@login_required
@admin_required
def workers_api():
    if request.method == 'POST':
        data = request.json
        name = data.get('name', '').strip()
        pin = data.get('pin', '').strip()
        role = data.get('role', 'barber')
        phone = data.get('phone', '').strip()
        email = data.get('email', '').strip()
        address = data.get('address', '').strip()
        if not name or not pin:
            return jsonify({'success': False, 'error': 'Name and PIN required'})
        # Check PIN unique
        existing = query("SELECT id FROM workers WHERE pin=? AND is_active=1", (pin,), one=True)
        if existing:
            return jsonify({'success': False, 'error': 'PIN already in use'})
        wid = execute("INSERT INTO workers (name, pin, role, phone, email, address) VALUES (?,?,?,?,?,?)", (name, pin, role, phone, email, address))
        return jsonify({'success': True, 'id': wid})
    workers = query("SELECT * FROM workers WHERE is_active=1 ORDER BY name")
    return jsonify([dict(w) for w in workers])

@app.route('/api/workers/<int:wid>', methods=['DELETE', 'PUT'])
@login_required
@admin_required
def worker_detail(wid):
    if request.method == 'DELETE':
        execute("UPDATE workers SET is_active=0 WHERE id=?", (wid,))
        return jsonify({'success': True})
    data = request.json
    execute("UPDATE workers SET name=?, pin=?, role=?, phone=?, email=?, address=? WHERE id=?",
            (data['name'], data['pin'], data['role'], data.get('phone', ''), data.get('email', ''), data.get('address', ''), wid))
    return jsonify({'success': True})

@app.route('/api/services', methods=['GET', 'POST'])
@login_required
def services_api():
    if request.method == 'POST':
        if session.get('worker_role') != 'admin':
            return jsonify({'success': False, 'error': 'Not authorized'})
        data = request.json
        sid = execute("INSERT INTO services (name, price, duration_minutes) VALUES (?,?,?)",
                      (data['name'], float(data['price']), int(data.get('duration', 30))))
        return jsonify({'success': True, 'id': sid})
    services = query("SELECT * FROM services WHERE is_active=1 ORDER BY name")
    return jsonify([dict(s) for s in services])

@app.route('/api/services/<int:sid>', methods=['DELETE', 'PUT'])
@login_required
@admin_required
def service_detail(sid):
    if request.method == 'DELETE':
        execute("UPDATE services SET is_active=0 WHERE id=?", (sid,))
        return jsonify({'success': True})
    data = request.json
    execute("UPDATE services SET name=?, price=?, duration_minutes=? WHERE id=?",
            (data['name'], float(data['price']), int(data.get('duration', 30)), sid))
    return jsonify({'success': True})

@app.route('/api/expenses', methods=['POST'])
@login_required
def add_expense():
    if session.get('worker_role') != 'admin':
        return jsonify({'success': False, 'error': 'Not authorized'})
    data = request.json
    eid = execute("INSERT INTO expenses (description, amount, category, added_by) VALUES (?,?,?,?)",
                  (data['description'], float(data['amount']), data.get('category', 'other'), session['worker_id']))
    return jsonify({'success': True, 'id': eid})

@app.route('/api/expenses/<int:eid>', methods=['DELETE'])
@login_required
@admin_required
def delete_expense(eid):
    execute("DELETE FROM expenses WHERE id=?", (eid,))
    return jsonify({'success': True})

@app.route('/api/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings_api():
    if request.method == 'POST':
        data = request.json
        for k, v in data.items():
            execute("INSERT OR REPLACE INTO shop_settings VALUES (?,?)", (k, v))
        return jsonify({'success': True})
    settings = query("SELECT * FROM shop_settings")
    return jsonify({s['key']: s['value'] for s in settings})

@app.route('/api/admin/job/<int:job_id>', methods=['DELETE'])
@login_required
@admin_required
def admin_delete_job(job_id):
    execute("DELETE FROM appointments WHERE id=?", (job_id,))
    return jsonify({'success': True})

@app.route('/api/upload-logo', methods=['POST'])
@login_required
@admin_required
def upload_logo():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'})
    # Validate extension
    allowed = {'png', 'jpg', 'jpeg', 'webp', 'svg'}
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in allowed:
        return jsonify({'success': False, 'error': 'Invalid file type. Use PNG, JPG, WEBP, or SVG'})
    # Save new logo
    uploads_dir = os.path.join(DATA_DIR, 'static', 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)
    for old in glob.glob(os.path.join(uploads_dir, 'logo.*')):
        os.remove(old)
    
    logo_path = os.path.join(uploads_dir, f'logo.{ext}')
    file.save(logo_path)
    return jsonify({'success': True})

@app.route('/api/backup-db')
@login_required
@admin_required
def backup_db():
    try:
        return send_file(DB_PATH, as_attachment=True, download_name=f"barbershop_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/restore-db', methods=['POST'])
@login_required
@admin_required
def restore_db():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file part'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No selected file'})
    
    if file:
        try:
            # Backup current DB before overwrite
            backup_path = DB_PATH + ".pre_restore"
            shutil.copy2(DB_PATH, backup_path)
            
            # Save new DB
            file.save(DB_PATH)
            return jsonify({'success': True})
        except Exception as e:
            # Try to restore from pre_restore if it failed
            if os.path.exists(DB_PATH + ".pre_restore"):
                shutil.copy2(DB_PATH + ".pre_restore", DB_PATH)
            return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    local_ip = get_local_ip()
    print(f"\n{'='*50}")
    print(f"  BarberShop Manager Running!")
    print(f"{'='*50}")
    print(f"  PC:     http://localhost:5000")
    print(f"  Mobile: http://{local_ip}:5000")
    print(f"  Admin PIN: 1234")
    print(f"{'='*50}\n")
    # Use debug=False in production/packaged app to avoid reloader issues
    is_prod = os.getenv('FLASK_ENV') == 'production' or getattr(sys, 'frozen', False)
    app.run(host='0.0.0.0', port=5000, debug=not is_prod)

# trigger reload
# trigger reload
# trigger reload
# trigger reload
# trigger reload
# trigger reload
# trigger reload# trigger reload
# trigger reload
# trigger reload
# trigger reload
# trigger reload
