import os
import sqlite3
from datetime import datetime, timedelta
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask import Flask, request, redirect, url_for, session, flash, render_template_string, abort, jsonify, send_from_directory

APP_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(APP_DIR, "lelong.db"))
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", os.path.join(APP_DIR, "static", "uploads"))
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "TUKAR_SECRET_KEY_INI_SEBELUM_PUBLISH")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("COOKIE_SECURE", "0") == "1"
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user'
        )""")
        con.execute("""CREATE TABLE IF NOT EXISTS cars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            starting_price INTEGER NOT NULL,
            image TEXT,
            seller_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            ends_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            FOREIGN KEY(seller_id) REFERENCES users(id)
        )""")
        con.execute("""CREATE TABLE IF NOT EXISTS bids (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            car_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(car_id) REFERENCES cars(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )""")
        # Create admin account on first run; change password after login.
        row = con.execute("SELECT id FROM users WHERE username='admin'").fetchone()
        if not row:
            con.execute(
                "INSERT INTO users(username,password_hash,role) VALUES(?,?,?)",
                ("admin", generate_password_hash("Admin123!"), "admin")
            )

def current_user():
    if not session.get("user_id"):
        return None
    with db() as con:
        return con.execute("SELECT id, username, role FROM users WHERE id=?", (session["user_id"],)).fetchone()

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            flash("Sila log masuk dahulu.")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def money(value):
    return "RM " + format(int(value), ",")

app.jinja_env.globals["money"] = money

STYLE = """
<style>
:root{--navy:#0b1730;--navy2:#13294b;--orange:#ff8a24;--green:#16734a;--ink:#172033;--muted:#667085;--line:#e4e9f1;--bg:#f5f7fb}
*{box-sizing:border-box}
body{font-family:Inter,Arial,sans-serif;margin:0;background:var(--bg);color:var(--ink);line-height:1.55}
header{background:linear-gradient(115deg,var(--navy),var(--navy2));color:white;padding:16px max(5%,calc((100% - 1120px)/2));display:flex;justify-content:space-between;gap:14px;align-items:center;flex-wrap:wrap;box-shadow:0 4px 18px #0b17301c}
header a{color:#e8eef8;text-decoration:none;margin:0 0 0 14px;font-size:14px}
header a:hover{color:var(--orange)}
.brand{font-size:21px;font-weight:800;letter-spacing:.2px;white-space:nowrap}
nav{display:flex;align-items:center;gap:4px;flex-wrap:wrap}
main{max-width:1120px;margin:28px auto;padding:0 18px;min-height:70vh}
.hero{background:radial-gradient(circle at 85% 20%,#2d5687 0,transparent 28%),linear-gradient(120deg,#0b1730,#183a65);color:white;border-radius:22px;padding:34px clamp(20px,5vw,48px);margin-bottom:28px;box-shadow:0 15px 36px #12284b20}
.hero h1{font-size:clamp(28px,4vw,42px);line-height:1.1;margin:0 0 12px;letter-spacing:-.8px}
.hero p{color:#d7e2f1;max-width:620px;margin:0 0 20px}
.hero form{display:flex;gap:10px;max-width:700px;flex-wrap:wrap}
.hero input{flex:1;min-width:200px;margin:0;background:white}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(245px,1fr));gap:20px}
.card,.box{background:white;border:1px solid var(--line);border-radius:16px;padding:17px;box-shadow:0 5px 20px #0b17300a}
.card{transition:transform .18s ease,box-shadow .18s ease}
.card:hover{transform:translateY(-3px);box-shadow:0 12px 28px #0b173016}
.card img{width:100%;height:190px;object-fit:cover;border-radius:11px;background:#e8edf4}
.card h3{font-size:19px;line-height:1.3;margin:13px 0 7px}
.card p{font-size:14px;color:#4f5c70}
.price{font-size:22px;font-weight:800;color:var(--green);margin:8px 0}
button,.btn{background:var(--orange);color:#1c2432;border:0;padding:11px 16px;border-radius:9px;cursor:pointer;text-decoration:none;display:inline-flex;align-items:center;justify-content:center;font-weight:750;font-size:14px;transition:filter .15s ease}
button:hover,.btn:hover{filter:brightness(.95)}
input,textarea{width:100%;padding:12px 13px;margin:7px 0 15px;border:1px solid #ccd5e2;border-radius:9px;font:inherit;background:#fff}
input:focus,textarea:focus{outline:3px solid #ff8a2433;border-color:var(--orange)}
input[type=file]{padding:9px}
label{font-weight:700;font-size:14px}
small,.muted{color:var(--muted)}
.flash{background:#fff4d7;border:1px solid #ffe2a0;color:#72500b;padding:12px 14px;border-radius:10px;margin-bottom:14px}
h2{letter-spacing:-.3px}
table{width:100%;border-collapse:collapse}
th{text-align:left;background:#f0f4f9}
td,th{border-bottom:1px solid var(--line);padding:10px}
footer{text-align:center;padding:26px 16px;color:var(--muted);font-size:13px}
@media(max-width:600px){header{padding:15px 18px}.brand{font-size:18px}header a{margin:0 10px 0 0}main{margin:18px auto;padding:0 13px}.hero{padding:25px 19px;border-radius:16px}.card img{height:175px}}
</style>
"""
LAYOUT = """
<!doctype html><html lang="ms"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{{ title }} | KHAIRUL AUTO LELONG</title>""" + STYLE + """</head><body>
<header><div class="brand">🚘 KHAIRUL AUTO LELONG</div><nav>
<a href="{{ url_for('index') }}">Utama</a>
{% if user %}<a href="{{ url_for('sell') }}">Iklankan Kereta</a>{% if user['role']=='admin' %}<a href="{{ url_for('admin') }}">Admin</a>{% endif %}<span>{{ user['username'] }}</span> · <a href="{{ url_for('logout') }}">Log keluar</a>
{% else %}<a href="{{ url_for('login') }}">Log masuk</a><a href="{{ url_for('register') }}">Daftar</a>{% endif %}
</nav></header><main>
{% with messages = get_flashed_messages() %}{% for message in messages %}<div class="flash">{{ message }}</div>{% endfor %}{% endwith %}
{{ content|safe }}
</main><footer>© {{ year }} KHAIRUL AUTO LELONG · Semak pemilikan dan dokumen kenderaan sebelum membida.</footer></body></html>
"""

def page(title, content):
    return render_template_string(LAYOUT, title=title, content=content, user=current_user(), year=datetime.now().year)

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)

@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    with db() as con:
        if q:
            cars = con.execute("""SELECT cars.*, users.username,
                COALESCE((SELECT MAX(amount) FROM bids WHERE bids.car_id=cars.id),cars.starting_price) AS current_bid
                FROM cars JOIN users ON users.id=cars.seller_id
                WHERE cars.status='active' AND (cars.title LIKE ? OR cars.description LIKE ?)
                ORDER BY cars.id DESC""", (f"%{q}%", f"%{q}%")).fetchall()
        else:
            cars = con.execute("""SELECT cars.*, users.username,
                COALESCE((SELECT MAX(amount) FROM bids WHERE bids.car_id=cars.id),cars.starting_price) AS current_bid
                FROM cars JOIN users ON users.id=cars.seller_id
                WHERE cars.status='active' ORDER BY cars.id DESC""").fetchall()
    cards = ""
    for car in cars:
        img = url_for("uploaded_file", filename=car["image"]) if car["image"] else ""
        image_html = f'<img src="{img}" alt="Gambar kereta">' if img else '<div style="height:180px;background:#e6eaf0;border-radius:8px;display:grid;place-items:center">Tiada gambar</div>'
        cards += f"""<article class="card">{image_html}<h3>{car['title']}</h3>
        <p class="price">{money(car['current_bid'])}</p><small>Bidaan semasa · Tamat: {car['ends_at']}</small>
        <p>{car['description'][:130]}</p><a class="btn" href="{url_for('car_detail', car_id=car['id'])}">Lihat / Bida</a></article>"""
    if not cards:
        cards = '<div class="box">Belum ada kereta disenaraikan. Log masuk dan pilih “Iklankan Kereta” untuk menambah iklan.</div>'
    content = f"""<section class="hero"><h1>Platform Lelong Kereta</h1><p>Cari kereta, semak harga bidaan dan iklankan kenderaan anda.</p>
    <form method="get"><input name="q" placeholder="Cari model, contoh: Hilux, Triton, D-Max" value="{q.replace('"','&quot;')}"><button>Cari kereta</button></form></section>
    <h2>Senarai kereta aktif</h2><div class="grid">{cards}</div>"""
    return page("Utama", content)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if len(username) < 3 or len(password) < 8:
            flash("Nama pengguna minimum 3 aksara dan kata laluan minimum 8 aksara.")
        else:
            try:
                with db() as con:
                    con.execute("INSERT INTO users(username,password_hash,role) VALUES(?,?,?)",
                                (username, generate_password_hash(password), "user"))
                flash("Akaun berjaya didaftarkan. Sila log masuk.")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                flash("Nama pengguna sudah digunakan.")
    content = """<div class="box" style="max-width:500px;margin:auto"><h2>Daftar akaun</h2><form method="post">
    <label>Nama pengguna</label><input name="username" required minlength="3">
    <label>Kata laluan (min. 8 aksara)</label><input type="password" name="password" required minlength="8">
    <button>Daftar</button></form></div>"""
    return page("Daftar", content)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        with db() as con:
            user = con.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            flash("Berjaya log masuk.")
            return redirect(url_for("index"))
        flash("Nama pengguna atau kata laluan salah.")
    content = """<div class="box" style="max-width:500px;margin:auto"><h2>Log masuk</h2><form method="post">
    <label>Nama pengguna</label><input name="username" required>
    <label>Kata laluan</label><input type="password" name="password" required>
    <button>Log masuk</button></form><p class="muted">Admin demo: admin / Admin123! (tukar sebelum digunakan sebenar)</p></div>"""
    return page("Log masuk", content)

@app.route("/logout")
def logout():
    session.clear()
    flash("Anda telah log keluar.")
    return redirect(url_for("index"))

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        try:
            price = int(request.form.get("starting_price", "0"))
            hours = int(request.form.get("hours", "24"))
        except ValueError:
            price, hours = 0, 24
        if not title or not description or price < 1 or hours < 1 or hours > 720:
            flash("Sila isi semua maklumat dengan betul. Tempoh bidaan 1 hingga 720 jam.")
        else:
            image_name = None
            file = request.files.get("image")
            if file and file.filename:
                if not allowed_file(file.filename):
                    flash("Format gambar mesti PNG, JPG, JPEG atau WEBP.")
                    return redirect(url_for("sell"))
                ext = secure_filename(file.filename).rsplit(".", 1)[1].lower()
                image_name = f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}.{ext}"
                file.save(os.path.join(UPLOAD_DIR, image_name))
            now = datetime.now()
            with db() as con:
                con.execute("""INSERT INTO cars(title,description,starting_price,image,seller_id,created_at,ends_at)
                    VALUES(?,?,?,?,?,?,?)""",
                    (title, description, price, image_name, session["user_id"],
                     now.isoformat(timespec="minutes"), (now + timedelta(hours=hours)).isoformat(timespec="minutes")))
            flash("Iklan berjaya ditambah.")
            return redirect(url_for("index"))
    content = """<div class="box" style="max-width:700px;margin:auto"><h2>Iklankan kereta</h2>
    <form method="post" enctype="multipart/form-data"><label>Tajuk / model kereta</label><input name="title" placeholder="Contoh: Toyota Hilux 2.4 2021" required>
    <label>Maklumat kereta dan status dokumen</label><textarea name="description" rows="5" placeholder="Tahun, keadaan, lokasi, dokumen dan syarat jualan" required></textarea>
    <label>Harga permulaan (RM)</label><input type="number" name="starting_price" min="1" required>
    <label>Tempoh bidaan (jam)</label><input type="number" name="hours" min="1" max="720" value="24" required>
    <label>Gambar kereta (maks. 5MB)</label><input type="file" name="image" accept=".png,.jpg,.jpeg,.webp">
    <button>Terbitkan iklan</button></form></div>"""
    return page("Iklankan kereta", content)

@app.route("/car/<int:car_id>")
def car_detail(car_id):
    with db() as con:
        car = con.execute("""SELECT cars.*, users.username,
            COALESCE((SELECT MAX(amount) FROM bids WHERE bids.car_id=cars.id),cars.starting_price) AS current_bid
            FROM cars JOIN users ON users.id=cars.seller_id WHERE cars.id=?""", (car_id,)).fetchone()
        bids = con.execute("""SELECT bids.amount,bids.created_at,users.username FROM bids
            JOIN users ON users.id=bids.user_id WHERE bids.car_id=? ORDER BY bids.amount DESC LIMIT 10""", (car_id,)).fetchall()
    if not car:
        abort(404)
    img = f'<img style="max-width:100%;max-height:360px;border-radius:10px" src="{url_for("uploaded_file", filename=car["image"])}">' if car["image"] else ""
    bid_rows = "".join(f"<li>{money(b['amount'])} — {b['username']} <small>({b['created_at']})</small></li>" for b in bids) or "<li>Belum ada bidaan.</li>"
    bid_form = ""
    if session.get("user_id") and session["user_id"] != car["seller_id"] and car["status"] == "active" and datetime.fromisoformat(car["ends_at"]) > datetime.now():
        bid_form = f"""<form method="post" action="{url_for('bid', car_id=car_id)}"><label>Jumlah bidaan (RM)</label>
        <input type="number" name="amount" min="{int(car['current_bid'])+1}" required><button>Hantar bidaan</button></form>"""
    elif not session.get("user_id"):
        bid_form = f'<p><a class="btn" href="{url_for("login")}">Log masuk untuk membida</a></p>'
    else:
        bid_form = "<p class='muted'>Bidaan tidak dibuka untuk iklan ini atau tempoh telah tamat.</p>"
    content = f"""<div class="box">{img}<h1>{car['title']}</h1><p class="price">Bidaan semasa: <span id="current-bid" data-value="{int(car['current_bid'])}">{money(car['current_bid'])}</span></p>
    <p>{car['description']}</p><p><b>Penjual:</b> {car['username']} · <b>Tamat:</b> {car['ends_at']}</p>{bid_form}
    <h3>10 bidaan tertinggi <small>(dikemas kini automatik)</small></h3><ol id="bid-history">{bid_rows}</ol>
    <p class="muted" id="live-status">Mengemas kini bidaan setiap 5 saat.</p>
    <script>
    async function refreshBids(){{try{{
      const r=await fetch("{url_for('api_car', car_id=car_id)}");
      if(!r.ok)return; const d=await r.json();
      const p=document.getElementById("current-bid");
      p.textContent=d.current_bid_label; p.dataset.value=d.current_bid;
      const input=document.querySelector('input[name="amount"]');
      if(input)input.min=String(d.current_bid+1);
      const list=document.getElementById("bid-history"); list.replaceChildren();
      if(!d.bids.length){{const li=document.createElement("li");li.textContent="Belum ada bidaan.";list.appendChild(li);}}
      for(const b of d.bids){{const li=document.createElement("li");li.textContent=b.amount_label+" — "+b.username+" ("+b.created_at+")";list.appendChild(li);}}
      document.getElementById("live-status").textContent="Dikemas kini: "+new Date().toLocaleTimeString();
    }}catch(e){{}}}}
    setInterval(refreshBids,5000);
    </script>
    <p><a class="btn" href="https://wa.me/?text={('Saya berminat dengan '+car['title']).replace(' ','%20')}" target="_blank" rel="noopener">Hubungi melalui WhatsApp</a></p></div>"""
    return page(car["title"], content)

@app.route("/api/car/<int:car_id>")
def api_car(car_id):
    with db() as con:
        car = con.execute("""SELECT id,starting_price,status,ends_at FROM cars WHERE id=?""", (car_id,)).fetchone()
        if not car:
            abort(404)
        top = con.execute("SELECT MAX(amount) AS top FROM bids WHERE car_id=?", (car_id,)).fetchone()["top"]
        current = max(car["starting_price"], top or 0)
        bids = con.execute("""SELECT bids.amount,bids.created_at,users.username FROM bids
            JOIN users ON users.id=bids.user_id WHERE bids.car_id=? ORDER BY bids.amount DESC LIMIT 10""", (car_id,)).fetchall()
    return jsonify({
        "current_bid": current,
        "current_bid_label": money(current),
        "status": car["status"],
        "ends_at": car["ends_at"],
        "bids": [{"amount": b["amount"], "amount_label": money(b["amount"]), "username": b["username"], "created_at": b["created_at"]} for b in bids]
    })

@app.route("/car/<int:car_id>/bid", methods=["POST"])
@login_required
def bid(car_id):
    try:
        amount = int(request.form.get("amount", "0"))
    except ValueError:
        amount = 0
    with db() as con:
        con.execute("BEGIN IMMEDIATE")
        car = con.execute("SELECT * FROM cars WHERE id=?", (car_id,)).fetchone()
        if not car:
            abort(404)
        highest = con.execute("SELECT MAX(amount) AS top FROM bids WHERE car_id=?", (car_id,)).fetchone()["top"]
        current = max(car["starting_price"], highest or 0)
        if car["seller_id"] == session["user_id"]:
            flash("Anda tidak boleh membida iklan sendiri.")
        elif car["status"] != "active" or datetime.fromisoformat(car["ends_at"]) <= datetime.now():
            flash("Tempoh bidaan telah tamat.")
        elif amount <= current:
            flash(f"Bidaan mesti lebih tinggi daripada {money(current)}.")
        else:
            con.execute("INSERT INTO bids(car_id,user_id,amount,created_at) VALUES(?,?,?,?)",
                        (car_id, session["user_id"], amount, datetime.now().isoformat(timespec="minutes")))
            flash("Bidaan direkodkan.")
    return redirect(url_for("car_detail", car_id=car_id))

@app.route("/admin")
@login_required
def admin():
    user = current_user()
    if not user or user["role"] != "admin":
        abort(403)
    with db() as con:
        cars = con.execute("""SELECT cars.*,users.username FROM cars JOIN users ON users.id=cars.seller_id
            ORDER BY cars.id DESC""").fetchall()
    rows = "".join(f"""<tr><td>{c['id']}</td><td>{c['title']}</td><td>{c['username']}</td><td>{money(c['starting_price'])}</td>
    <td>{c['status']}</td><td><form method="post" action="{url_for('toggle_car',car_id=c['id'])}"><button>{'Aktifkan' if c['status']!='active' else 'Tutup iklan'}</button></form></td></tr>""" for c in cars)
    content = f"""<div class="box"><h2>Panel admin</h2><p>Semak dan tutup iklan yang tidak sesuai.</p>
    <div style="overflow-x:auto"><table cellpadding="10"><tr><th>ID</th><th>Kereta</th><th>Penjual</th><th>Harga mula</th><th>Status</th><th>Tindakan</th></tr>{rows}</table></div></div>"""
    return page("Admin", content)

@app.route("/admin/car/<int:car_id>/toggle", methods=["POST"])
@login_required
def toggle_car(car_id):
    user = current_user()
    if not user or user["role"] != "admin":
        abort(403)
    with db() as con:
        car = con.execute("SELECT status FROM cars WHERE id=?", (car_id,)).fetchone()
        if not car:
            abort(404)
        new_status = "closed" if car["status"] == "active" else "active"
        con.execute("UPDATE cars SET status=? WHERE id=?", (new_status, car_id))
    flash("Status iklan dikemas kini.")
    return redirect(url_for("admin"))

@app.errorhandler(413)
def too_large(_):
    return page("Fail terlalu besar", "<div class='box'>Gambar melebihi had 5MB. Sila cuba gambar lebih kecil.</div>"), 413

init_db()

if __name__ == "__main__":
    # Local testing. Hosted services provide PORT; production should run via gunicorn.
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
