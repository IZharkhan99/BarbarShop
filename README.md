# ✂ BarberShop Manager

A professional barber shop management system — runs on your PC, workers use their phones.

## Quick Start

### Requirements
- Python 3.8+
- Flask (auto-installed)

### Run the App

**Option 1 – Double-click start.py**  
Or from terminal:
```bash
python start.py
```

**Option 2 – Direct Flask run:**
```bash
pip install flask
python app.py
```

## Access

| Device | URL |
|--------|-----|
| PC | http://localhost:5000 |
| Worker Phones | http://YOUR-PC-IP:5000 |

> **Find your PC IP:** Windows → `ipconfig` → IPv4 Address  
> Make sure all phones are on the same WiFi network!

## Default Login

| User | PIN |
|------|-----|
| Admin | 1234 |

**Change the admin PIN in Settings after first login!**

## Features

### For Workers (Phone)
- PIN-based login (no username needed)
- Log jobs with one tap
- Choose from service menu
- Record payment method (cash / card / online)
- See today's earnings and job count
- Delete mistakes from today

### For Admin (PC or Phone)
- Full overview dashboard
- Today's revenue, expenses, net profit
- Per-worker performance
- Add/remove workers and services
- Log shop expenses by category
- Generate date-range reports
- Shop settings (name, currency, PIN)

## Data Storage

All data is stored in `barbershop.db` (SQLite) — no internet required.  
Back up this file regularly to keep your records safe.

## Network Setup Tips

- Run the server PC on a wired connection or strong WiFi
- Make sure Windows Firewall allows port 5000 (or add an exception)
- Workers open the browser on their phones — no app install needed
- Bookmark the URL on their phones for easy access

## Structure

```
barbershop/
├── app.py          ← Main Flask application
├── start.py        ← Easy startup script
├── requirements.txt
├── barbershop.db   ← Auto-created database
└── templates/
    ├── login.html  ← PIN login screen
    ├── worker.html ← Worker mobile dashboard
    └── dashboard.html ← Admin panel
```
