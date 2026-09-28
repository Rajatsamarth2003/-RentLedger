# 🏠 RentLedger

> **A simple, practical rent & electricity management system for rental properties.**

RentLedger is a Flask-based property desk application designed to make monthly rent and electricity billing easier to manage. It keeps **families, meter readings, electricity rates, monthly bills, history, and PDF statements** together in one place.

---

## ✨ Features

| Feature | Description |
|---|---|
| 👨‍👩‍👧‍👦 Family Management | Add and manage rental families by name |
| 🏠 Active / Moved-out Status | Preserve old records when a family leaves |
| 💰 Manual Monthly Rent | Enter or change rent every month |
| ⚡ Flexible Electricity Rate | Select ₹11–₹20 per unit each month |
| 📷 Meter Photo | Upload a meter image |
| 🔎 OCR Cross-check | Use EasyOCR as an additional reading check |
| 🧮 Unit Calculation | Calculate units from previous/current readings |
| ✍️ Manual Unit Check | Enter verified units manually |
| 🧾 Monthly Statement | Generate a statement for a family |
| 🖨️ PDF / Print | Create printable monthly statements |
| 📚 Bill History | Preserve saved monthly bills |
| 📊 Monthly Report | Review monthly totals |
| 🔐 Authentication | Login and registration |


# 🧮 Billing Logic

### Meter Units

```text
Meter Units = Current Meter Reading - Previous Meter Reading
```

### Electricity Amount

```text
Electricity Amount = Entered Units × Selected Rate
```

### Total Payable

```text
Total Payable = Monthly Rent + Electricity Amount
```

### Example

```text
Previous Reading = 1155
Current Reading  = 1214

Units Used = 1214 - 1155
           = 59 units

Electricity Rate = ₹12 / unit
Rent              = ₹4,700

Electricity = 59 × ₹12
            = ₹708

Total = ₹4,700 + ₹708
      = ₹5,408
```

---

# ⚡ Electricity Rate

The rate is selected for each monthly bill:

```text
₹11  ₹12  ₹13  ₹14  ₹15
₹16  ₹17  ₹18  ₹19  ₹20
```

Rent is also entered manually every month, so rent can change without affecting previous bills.

---

# 📷 Meter Photo + OCR Workflow

```text
Upload Meter Photo
        ↓
     OCR Scan
        ↓
Detected Reading
        ↓
Compare with Manual Reading
        ↓
Check Previous Reading
        ↓
Calculate Units
        ↓
Verify Units
        ↓
Calculate Electricity
        ↓
Add Monthly Rent
        ↓
Generate Bill
```

> **Important:** OCR is only a cross-check. Always verify the detected meter reading before saving.

For better OCR results, use a clear, straight, well-lit photo focused on the meter digits.

---

# 👥 Family Management

Each family has its own identity and billing history.

Example:

```text
F001 — Sandeep Dada
F002 — ABC Family
F003 — New Family
```

When a family moves out:

```text
Old Family
   ↓
Moved out
   ↓
Historical bills preserved
   ↓
New Family added
   ↓
New monthly records
```

This prevents old billing records from being mixed with a new resident.

---

# 🔐 Authentication

RentLedger includes login and registration.

### Local default account

```text
Username: admin
Password: RentLedger@123
```

New users can use **Create an account** and register with:

```text
Username
Password
Confirm Password
```

Passwords are stored using password hashing rather than plain text.

> **For public deployment:** change the default admin password and use a strong secret key.

---

# 🗃️ Data Storage

RentLedger uses SQLite for local storage.

The application can maintain:

```text
Users
Families
Monthly Bills
Meter Readings
Electricity Rates
Units
Rent
Bill History
```

---

# 📁 Project Structure

```text
rent_bill_manager/
│
├── .venv/
├── app.py
├── config.py
├── requirements.txt
│
├── database/
│   ├── db.py
│   └── rent_manager.db
│
├── models/
├── services/
├── templates/
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
├── uploads/
│   └── meter_images/
│
├── generated_bills/
│   └── pdf/
│
└── tests/
```

---

# 🛠️ Tech Stack

### Backend
- Python
- Flask
- SQLite

### Frontend
- HTML
- CSS
- JavaScript
- Jinja templates

### OCR & Images
- EasyOCR
- Pillow

### PDF
- ReportLab

### Development
- Python virtual environment
- VS Code
- PowerShell

---

# 🚀 Installation

## Windows

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

If the terminal already shows:

```text
(.venv)
```

the virtual environment is already active.

Open:

```text
http://127.0.0.1:5000
```

---

# 🧾 Monthly Workflow

```text
Login
  ↓
Select Family
  ↓
Upload Meter Photo
  ↓
Check OCR Reading
  ↓
Enter / Verify Current Reading
  ↓
Verify Previous Reading
  ↓
Confirm Units
  ↓
Select Electricity Rate
  ↓
Enter Monthly Rent
  ↓
Review Bill
  ↓
Save
  ↓
Generate PDF
  ↓
Print / Share
```

---

# 🔎 Verification

RentLedger intentionally keeps manual verification in the workflow.

```text
Meter Calculated Units
        VS
Manually Entered Units
```

The **manually verified units** are used for billing.

```text
Manual Units × Selected Rate = Electricity Amount
```

This provides an extra check before a bill is saved.

---

# 📄 Monthly Statement

A statement contains:

```text
Family Name
Billing Month

Previous Meter Reading
Current Meter Reading
Meter Calculated Units
Units Entered
Electricity Rate
Monthly Rent
Electricity Amount
TOTAL PAYABLE
```

---

# 🔒 Production Notes

Before deploying publicly:

- Change the default admin password
- Set a strong `SECRET_KEY`
- Do not run Flask debug mode publicly
- Use HTTPS
- Keep database backups
- Protect uploaded meter images
- Store secrets in environment variables
- Use a production WSGI server

---

# 🧪 Testing Checklist

- [ ] Create a new account
- [ ] Login
- [ ] Show / hide password
- [ ] Add a family
- [ ] Delete a family
- [ ] Upload meter photo
- [ ] Run OCR
- [ ] Enter previous reading
- [ ] Enter current reading
- [ ] Verify units
- [ ] Select electricity rate
- [ ] Enter monthly rent
- [ ] Save bill
- [ ] Check bill history
- [ ] Check monthly report
- [ ] Generate PDF
- [ ] Print statement
- [ ] Verify old family records remain available

---

# 🌱 Future Improvements

Possible future versions:

- 📱 Mobile-friendly meter entry
- 🔔 Monthly billing reminders
- 📊 Yearly income and electricity analytics
- 📤 WhatsApp / email statement sharing
- 💾 Automatic database backup
- ☁️ Cloud database
- 👤 Multiple property managers
- 🔐 Role-based access
- 🧾 Paid / Pending / Partial payment status
- 📈 Family-wise billing charts
- 🔍 Search and filters

---

## 💡 RentLedger

> **Small details matter. Keep every month's reading, rent and rate together.**

**Project:** RentLedger  
**Category:** Property / Rental Management  
**Backend:** Flask + SQLite  
**PDF:** ReportLab  
**OCR:** EasyOCR
