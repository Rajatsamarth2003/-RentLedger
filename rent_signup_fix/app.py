import os
import glob
from datetime import datetime

from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, jsonify, send_file, session
)
from functools import wraps
import hashlib
import hmac

from config import (
    UPLOAD_FOLDER, PDF_FOLDER,
    MIN_ELECTRICITY_RATE, MAX_ELECTRICITY_RATE,
    ADMIN_USERNAME, ADMIN_PASSWORD_HASH
)
from database.db import get_db, init_db
from services.calculator import calculate_bill
from services.ocr_service import extract_meter_reading
from services.pdf_service import generate_bill_pdf

app = Flask(__name__)
app.secret_key = os.environ.get("RENTLEDGER_SECRET_KEY", "change-this-secret-key-before-production")


def verify_password(password, stored_hash):
    try:
        method, salt, expected = stored_hash.split("$", 2)
        iterations = int(method.split(":")[-1])
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations).hex()
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def hash_password(password):
    iterations = 600000
    salt = os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), iterations
    ).hex()
    return f"pbkdf2:sha256:{iterations}${salt}${digest}"


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped_view


@app.before_request
def require_login():
    public_endpoints = {"login", "signup", "static"}
    if request.endpoint not in public_endpoints and not session.get("logged_in"):
        return redirect(url_for("login", next=request.path))


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("logged_in"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username=?", (username,)
        ).fetchone()
        db.close()

        if user and verify_password(password, user["password_hash"]):
            session.clear()
            session["logged_in"] = True
            session["username"] = user["username"]
            session["user_id"] = user["id"]
            next_url = request.args.get("next") or request.form.get("next")
            if not next_url or not next_url.startswith("/"):
                next_url = url_for("dashboard")
            return redirect(next_url)

        flash("Invalid username or password.", "error")

    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if session.get("logged_in"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if len(username) < 3 or len(username) > 40:
            flash("Username must be between 3 and 40 characters.", "error")
            return redirect(url_for("signup"))

        if not username.replace("_", "").replace("-", "").isalnum():
            flash("Username can contain only letters, numbers, hyphens and underscores.", "error")
            return redirect(url_for("signup"))

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return redirect(url_for("signup"))

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("signup"))

        db = get_db()
        existing = db.execute(
            "SELECT id FROM users WHERE lower(username)=lower(?)", (username,)
        ).fetchone()

        if existing:
            db.close()
            flash("That username is already registered. Please sign in.", "error")
            return redirect(url_for("login"))

        db.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, hash_password(password))
        )
        db.commit()
        db.close()

        flash("Account created successfully. You can now sign in.", "success")
        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PDF_FOLDER, exist_ok=True)

init_db()


def allowed_image(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in {"png", "jpg", "jpeg", "webp"}
    )


@app.context_processor
def inject_globals():
    return {
        "current_year": datetime.now().year,
        "min_rate": MIN_ELECTRICITY_RATE,
        "max_rate": MAX_ELECTRICITY_RATE,
    }


@app.route("/")
def dashboard():
    db = get_db()

    active_families = db.execute(
        "SELECT * FROM families WHERE status='Active' ORDER BY name"
    ).fetchall()

    # Keep the top cards as an overall snapshot, while the family overview
    # below gives each family its own independent totals.
    stats = db.execute("""
        SELECT
            COUNT(*) AS bill_count,
            COALESCE(SUM(total_amount), 0) AS total_billed,
            COALESCE(SUM(electricity_bill), 0) AS total_electricity,
            COALESCE(SUM(entered_units), 0) AS total_units
        FROM bills
    """).fetchone()

    family_overviews = db.execute("""
        SELECT
            families.*,
            COUNT(bills.id) AS bill_count,
            COALESCE(SUM(bills.rent), 0) AS total_rent,
            COALESCE(SUM(bills.electricity_bill), 0) AS total_electricity,
            COALESCE(SUM(bills.entered_units), 0) AS total_units,
            COALESCE(SUM(bills.total_amount), 0) AS total_billed,
            MAX(bills.month) AS last_bill_month
        FROM families
        LEFT JOIN bills ON bills.family_id = families.id
        GROUP BY families.id
        ORDER BY CASE WHEN families.status = 'Active' THEN 0 ELSE 1 END, families.name
    """).fetchall()

    recent_bills = db.execute("""
        SELECT bills.*, families.name AS family_name
        FROM bills
        JOIN families ON families.id = bills.family_id
        ORDER BY bills.id DESC
        LIMIT 8
    """).fetchall()

    return render_template(
        "dashboard.html",
        families=active_families,
        family_overviews=family_overviews,
        stats=stats,
        recent_bills=recent_bills
    )


@app.route("/families")
def families():
    db = get_db()
    rows = db.execute("""
        SELECT
            families.*,
            COUNT(bills.id) AS bill_count
        FROM families
        LEFT JOIN bills ON bills.family_id = families.id
        GROUP BY families.id
        ORDER BY status='Active' DESC, name
    """).fetchall()
    return render_template("families/list.html", families=rows)


@app.route("/families/add", methods=["GET", "POST"])
def add_family():
    if request.method == "POST":
        name = request.form["name"].strip()
        default_rent = float(request.form["default_rent"] or 0)
        move_in_date = request.form["move_in_date"]

        if not name:
            flash("Please enter a family name.", "error")
            return redirect(request.url)

        db = get_db()
        db.execute("""
            INSERT INTO families (name, default_rent, move_in_date, status)
            VALUES (?, ?, ?, 'Active')
        """, (name, default_rent, move_in_date))
        db.commit()

        flash(f"{name} has been added.", "success")
        return redirect(url_for("families"))

    return render_template("families/add.html")


@app.route("/families/<int:family_id>")
def family_details(family_id):
    db = get_db()
    family = db.execute(
        "SELECT * FROM families WHERE id=?", (family_id,)
    ).fetchone()

    if not family:
        flash("Family not found.", "error")
        return redirect(url_for("families"))

    bills = db.execute("""
        SELECT * FROM bills
        WHERE family_id=?
        ORDER BY month DESC, id DESC
    """, (family_id,)).fetchall()

    totals = db.execute("""
        SELECT
            COALESCE(SUM(total_amount), 0) AS total_amount,
            COALESCE(SUM(electricity_bill), 0) AS electricity,
            COALESCE(SUM(entered_units), 0) AS units
        FROM bills
        WHERE family_id=?
    """, (family_id,)).fetchone()

    return render_template(
        "families/details.html",
        family=family,
        bills=bills,
        totals=totals
    )


@app.route("/families/<int:family_id>/deactivate", methods=["POST"])
def deactivate_family(family_id):
    move_out_date = request.form["move_out_date"]

    db = get_db()
    db.execute("""
        UPDATE families
        SET status='Inactive', move_out_date=?
        WHERE id=?
    """, (move_out_date, family_id))
    db.commit()

    flash("Family moved to inactive status. Their history remains safe.", "success")
    return redirect(url_for("families"))


@app.route("/families/<int:family_id>/delete", methods=["POST"])
def delete_family(family_id):
    db = get_db()
    family = db.execute(
        "SELECT * FROM families WHERE id=?", (family_id,)
    ).fetchone()

    if not family:
        flash("Family not found.", "error")
        return redirect(url_for("families"))

    bill_count = db.execute(
        "SELECT COUNT(*) AS count FROM bills WHERE family_id=?", (family_id,)
    ).fetchone()["count"]

    # A family with saved bills cannot be hard-deleted because the old
    # statements must remain available in Bill history.
    if bill_count:
        flash(
            "This family has saved bills, so it cannot be deleted. Mark the family moved out instead to keep the history.",
            "error"
        )
        return redirect(url_for("family_details", family_id=family_id))

    for image_path in glob.glob(os.path.join(UPLOAD_FOLDER, f"family_{family_id}_*")):
        try:
            os.remove(image_path)
        except OSError:
            pass

    db.execute("DELETE FROM families WHERE id=?", (family_id,))
    db.commit()

    flash(f"{family['name']} has been deleted.", "success")
    return redirect(url_for("families"))


@app.route("/bills/create/<int:family_id>", methods=["GET", "POST"])
def create_bill(family_id):
    db = get_db()

    family = db.execute(
        "SELECT * FROM families WHERE id=?", (family_id,)
    ).fetchone()

    if not family:
        flash("Family not found.", "error")
        return redirect(url_for("families"))

    selected_month = request.args.get("month") or datetime.now().strftime("%Y-%m")

    def get_previous_reading(billing_month):
        row = db.execute("""
            SELECT current_reading, month
            FROM bills
            WHERE family_id=? AND month < ?
            ORDER BY month DESC, id DESC
            LIMIT 1
        """, (family_id, billing_month)).fetchone()
        return row["current_reading"] if row else 0

    previous_reading = get_previous_reading(selected_month)

    if request.method == "POST":
        month = request.form["month"]
        rent = float(request.form["rent"])
        current_reading = float(request.form["current_reading"])
        units = float(request.form["units"])
        rate = float(request.form["rate"])

        # Previous reading is always derived from the latest saved reading
        # before the selected billing month. It is never copied from the
        # current month's reading.
        previous_reading = get_previous_reading(month)

        duplicate = db.execute("""
            SELECT id FROM bills
            WHERE family_id=? AND month=?
            LIMIT 1
        """, (family_id, month)).fetchone()
        if duplicate:
            flash("A bill for this family and month already exists. Open the existing bill from Bill history.", "error")
            return redirect(url_for("bill_history"))

        ocr_reading_raw = request.form.get("ocr_reading", "").strip()
        ocr_confidence_raw = request.form.get("ocr_confidence", "").strip()

        if rent < 0 or units < 0 or current_reading < 0:
            flash("Rent, units and reading cannot be negative.", "error")
            return redirect(request.url)

        if not (MIN_ELECTRICITY_RATE <= rate <= MAX_ELECTRICITY_RATE):
            flash("Please select a rate between ₹11 and ₹20.", "error")
            return redirect(request.url)

        if not month:
            flash("Please select a billing month.", "error")
            return redirect(request.url)

        calculated_units = current_reading - previous_reading

        if calculated_units < 0:
            flash("Current reading cannot be lower than the previous reading.", "error")
            return redirect(request.url)

        bill = calculate_bill(rent, rate, units)

        image_path = None
        image = request.files.get("meter_image")

        if image and image.filename:
            if not allowed_image(image.filename):
                flash("Please upload JPG, JPEG, PNG or WEBP image.", "error")
                return redirect(request.url)

            safe_name = os.path.basename(image.filename).replace(" ", "_")
            filename = f"family_{family_id}_{month}_{safe_name}"
            image_path = os.path.join(UPLOAD_FOLDER, filename)
            image.save(image_path)

        ocr_reading = float(ocr_reading_raw) if ocr_reading_raw else None
        ocr_confidence = float(ocr_confidence_raw) if ocr_confidence_raw else None

        cursor = db.execute("""
            INSERT INTO bills (
                family_id, month, previous_reading, current_reading,
                calculated_units, entered_units, electricity_rate,
                rent, electricity_bill, total_amount,
                meter_image, ocr_reading, ocr_confidence
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            family_id, month, previous_reading, current_reading,
            calculated_units, units, rate,
            bill["rent"], bill["electricity"], bill["total"],
            image_path, ocr_reading, ocr_confidence
        ))

        db.commit()
        return redirect(url_for("view_bill", bill_id=cursor.lastrowid))

    return render_template(
        "bills/create.html",
        family=family,
        previous_reading=previous_reading,
        selected_month=selected_month
    )


@app.route("/families/<int:family_id>/previous-reading")
def previous_reading_api(family_id):
    month = request.args.get("month", "").strip()
    if not month:
        return jsonify(success=False, message="Billing month is required."), 400

    db = get_db()
    family = db.execute("SELECT id FROM families WHERE id=?", (family_id,)).fetchone()
    if not family:
        return jsonify(success=False, message="Family not found."), 404

    row = db.execute("""
        SELECT current_reading, month
        FROM bills
        WHERE family_id=? AND month < ?
        ORDER BY month DESC, id DESC
        LIMIT 1
    """, (family_id, month)).fetchone()

    return jsonify(
        success=True,
        previous_reading=float(row["current_reading"]) if row else 0,
        source_month=row["month"] if row else None
    )


@app.route("/ocr", methods=["POST"])
def ocr_meter():
    image = request.files.get("meter_image")

    if not image or not image.filename:
        return jsonify(success=False, message="Please select a meter image."), 400

    if not allowed_image(image.filename):
        return jsonify(success=False, message="Unsupported image format."), 400

    temp_dir = os.path.join(UPLOAD_FOLDER, "_ocr_temp")
    os.makedirs(temp_dir, exist_ok=True)

    filename = os.path.basename(image.filename).replace(" ", "_")
    temp_path = os.path.join(temp_dir, filename)
    image.save(temp_path)

    try:
        result = extract_meter_reading(temp_path)
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass

    return jsonify(
        success=result.get("reading") is not None,
        reading=result.get("reading"),
        confidence=result.get("confidence"),
        raw_text=result.get("raw_text", ""),
        message=result.get("error", "")
    )


@app.route("/bills/<int:bill_id>")
def view_bill(bill_id):
    db = get_db()
    bill = db.execute("""
        SELECT bills.*, families.name AS family_name
        FROM bills
        JOIN families ON families.id = bills.family_id
        WHERE bills.id=?
    """, (bill_id,)).fetchone()

    if not bill:
        flash("Bill not found.", "error")
        return redirect(url_for("dashboard"))

    difference = bill["entered_units"] - bill["calculated_units"]

    return render_template(
        "bills/view.html",
        bill=bill,
        difference=difference
    )


@app.route("/bills/history")
def bill_history():
    db = get_db()
    bills = db.execute("""
        SELECT bills.*, families.name AS family_name
        FROM bills
        JOIN families ON families.id = bills.family_id
        ORDER BY bills.month DESC, bills.id DESC
    """).fetchall()

    return render_template("bills/history.html", bills=bills)


@app.route("/reports/monthly")
def monthly_report():
    month = request.args.get("month", datetime.now().strftime("%Y-%m"))

    db = get_db()
    bills = db.execute("""
        SELECT bills.*, families.name AS family_name
        FROM bills
        JOIN families ON families.id = bills.family_id
        WHERE bills.month=?
        ORDER BY families.name
    """, (month,)).fetchall()

    summary = db.execute("""
        SELECT
            COALESCE(SUM(rent), 0) AS rent,
            COALESCE(SUM(electricity_bill), 0) AS electricity,
            COALESCE(SUM(total_amount), 0) AS total,
            COALESCE(SUM(entered_units), 0) AS units
        FROM bills
        WHERE month=?
    """, (month,)).fetchone()

    return render_template(
        "reports/monthly.html",
        month=month,
        bills=bills,
        summary=summary
    )


@app.route("/bills/<int:bill_id>/pdf")
def bill_pdf(bill_id):
    db = get_db()
    bill = db.execute("""
        SELECT bills.*, families.name AS family_name
        FROM bills
        JOIN families ON families.id = bills.family_id
        WHERE bills.id=?
    """, (bill_id,)).fetchone()

    if not bill:
        flash("Bill not found.", "error")
        return redirect(url_for("dashboard"))

    safe_family = "".join(
        c if c.isalnum() else "_" for c in bill["family_name"]
    )
    filename = f"{safe_family}_{bill['month']}.pdf"
    output_path = os.path.join(PDF_FOLDER, filename)

    generate_bill_pdf(dict(bill), output_path)

    return send_file(
        output_path,
        as_attachment=True,
        download_name=filename
    )


if __name__ == "__main__":
    app.run(debug=True)
